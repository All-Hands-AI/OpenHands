import asyncio
import copy
import functools
import json
import multiprocessing
import os
import tempfile
import docker
from typing import Any, Literal

import pandas as pd
import toml
from datasets import load_dataset

import openhands.agenthub
from evaluation.benchmarks.swe_bench.binary_patch_utils import (
    remove_binary_diffs,
    remove_binary_files_from_git,
)
from evaluation.benchmarks.swe_bench.resource.mapping import (
    get_instance_resource_factor,
)
from evaluation.utils.shared import (
    EvalException,
    EvalMetadata,
    EvalOutput,
    assert_and_raise,
    codeact_user_response,
    get_default_sandbox_config_for_eval,
    get_metrics,
    is_fatal_evaluation_error,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
    update_llm_config_for_completions_logging,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AgentConfig,
    OpenHandsConfig,
    get_llm_config_arg,
    get_evaluation_parser,
)
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.core.config.utils import get_condenser_config_arg
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.critic import AgentFinishedCritic
from openhands.events.action import CmdRunAction, FileReadAction, MessageAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
)
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync
from openhands.utils.shutdown_listener import sleep_if_should_continue

USE_HINT_TEXT = os.environ.get('USE_HINT_TEXT', 'false').lower() == 'true'
RUN_WITH_BROWSING = os.environ.get('RUN_WITH_BROWSING', 'false').lower() == 'true'
BenchMode = Literal['swe', 'swt', 'swt-ci']


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}


def _get_swebench_workspace_dir_name(instance: pd.Series) -> str:
    return f'{instance.repo}__{instance.version}'.replace('/', '__')


def get_instruction(instance: pd.Series, metadata: EvalMetadata) -> MessageAction:
    workspace_dir_name = _get_swebench_workspace_dir_name(instance)

    # TODO: Change to testbed?
    instruction = f"""
<uploaded_files>
/workspace/{workspace_dir_name}
</uploaded_files>

I’ve uploaded a python code repository in the directory workspace_dir_name. Consider the following performance workload and `workload()` function showing an specific usage of the repository:
<performance_workload>
{instance.workload}
</performance_workload>

Can you help me implement the necessary changes to the repository so that the runtime of the `workload()` function is faster? Basic guidelines:
1. Your task is to make changes to non-test files in the /workspace directory to improve the performance of the code running in `workload()`. Please do not directly change the implementation of the `workload()` function to optimize things: I want you to focus on making the workload AS IS run faster by only editing the repository containing code that the `workload()` function calls.
2. Make changes while ensuring the repository is functionally equivalent to the original: your changes should not introduce new bugs or cause already-passing tests to begin failing after your changes. However, you do not need to worry about tests that already fail without any changes made. For relevant test files you find in the repository, you can run them via the bash command `{instance.test_cmd} <test_file>` to check for correctness. Note that running all the tests may take a long time, so you need to determine which tests are relevant to your changes.
3. Make sure the `workload()` function improves in performance after you make changes to the repository. The workload can potentially take some time to run, so please allow it to finish and be generous with setting your timeout parameter (a timeout value of 3600 or larger here is encouraged): for faster iteration, you should adjust the workload script to use fewer iterations. Before you complete your task, please make sure to check that the **original performance workload** and `workload()` function runs successfully and the performance is improved.
4. You may need to reinstall/rebuild the repo for your changes to take effect before testing if you made non-Python changes. Reinstalling may take a long time to run (a timeout value of 3600 or larger here is encouraged), so please be patient with running it and allow it to complete if possible. You can reinstall the repository by running the bash command `{instance.rebuild_cmd}` in the workspace directory.
5. All the dependencies required to run the `workload()` function are already installed in the environment. You should not install or upgrade any dependencies.

Follow these steps to improve performance:
1. As a first step, explore the repository structure.
2. Create a Python script to reproduce the performance workload, execute it with python <workload_file>, and examine the printed output metrics.
3. Edit the source code of the repository to improve performance. Please do not change the contents of the `workload()` function itself, but focus on optimizing the code in the repository that the original `workload()` function uses.
4. If non-Python changes were made, rebuild the repo to make sure the changes take effect.
5. Rerun your script to confirm that performance has improved.
6. If necessary, identify any relevant test files in the repository related to your changes and verify that test statuses did not change after your modifications.
7. After each attempted change, please reflect on the changes attempted and the performance impact observed. If the performance did not improve, consider alternative approaches or optimizations.
8. Once you are satisfied, please use the finish command to complete your task.

Please remember that you should not change the implementation of the `workload()` function. The performance improvement should solely come from editing the source files in the code repository.
"""

    if RUN_WITH_BROWSING:
        instruction += (
            '<IMPORTANT!>\nYou SHOULD NEVER attempt to browse the web. </IMPORTANT!>\n'
        )

    return MessageAction(content=instruction)



def get_instance_docker_image(
    instance_id: str,
) -> str:
    # TODO: This currently assumes docker image is already slocal.
    return f"ghcr.io/swefficiency/swefficiency-images:{instance_id}"
    # return f"docker.io/swefficiency/swefficiency:{instance_id}"


def get_config(
    instance: pd.Series,
    metadata: EvalMetadata,
    cpu_group: list[int] | None = None,
) -> OpenHandsConfig:
    # We use a different instance image for the each instance of swe-bench eval
    base_container_image = get_instance_docker_image(
        instance['instance_id'],
    )
    logger.info(
        f'Using instance container image: {base_container_image}. '
        f'Please make sure this image exists. '
        f'Submit an issue on https://github.com/All-Hands-AI/OpenHands if you run into any issues.'
    )

    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = base_container_image
    sandbox_config.enable_auto_lint = True
    sandbox_config.use_host_network = False
    sandbox_config.timeout = 3600

    # Control container cleanup behavior via environment variable
    # Default to False for multiprocessing stability to prevent cascade failures
    sandbox_config.rm_all_containers = True

    sandbox_config.platform = 'linux/amd64'
    sandbox_config.remote_runtime_resource_factor = 4.0
    sandbox_config.runtime_startup_env_vars.update(
        {
            "NO_CHANGE_TIMEOUT_SECONDS": '900',  # 15 minutes
        }
    )

    if cpu_group is not None:
        print(f'Configuring Docker runtime with CPU group: {cpu_group}')
        sandbox_config.docker_runtime_kwargs = {
            # HACK: Use the cpu_group if provided, otherwise use all available CPUs
            "cpuset_cpus": ','.join(map(str, cpu_group)),
            "nano_cpus": int(1e9 * len(cpu_group)),  # optional: hard cap to vCPU count
            "mem_limit": "16g",
        }

    # Note: We keep rm_all_containers = False for worker process safety

    config = OpenHandsConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        max_iterations=metadata.max_iterations,
        runtime=os.environ.get('RUNTIME', 'docker'),
        sandbox=sandbox_config,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(
        update_llm_config_for_completions_logging(
            metadata.llm_config, metadata.eval_output_dir, instance['instance_id']
        )
    )
    agent_config = AgentConfig(
        enable_jupyter=False,
        enable_browsing=RUN_WITH_BROWSING,
        enable_llm_editor=False,
        enable_mcp=False,
        condenser=metadata.condenser_config,
        enable_prompt_extensions=False,
    )
    config.set_agent_config(agent_config)
    return config


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
    metadata: EvalMetadata,
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info('-' * 30)
    logger.info('BEGIN Runtime Initialization Fn')
    logger.info('-' * 30)
    workspace_dir_name = _get_swebench_workspace_dir_name(instance)
    obs: CmdOutputObservation

    # Set instance id and git configuration
    action = CmdRunAction(
        command=f"""echo 'export SWE_INSTANCE_ID={instance['instance_id']}' >> ~/.bashrc && echo 'export PIP_CACHE_DIR=~/.cache/pip' >> ~/.bashrc && echo "alias git='git --no-pager'" >> ~/.bashrc && git config --global core.pager "" && git config --global diff.binary false"""
    )
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to export SWE_INSTANCE_ID and configure git: {str(obs)}',
    )

    action = CmdRunAction(command="""export USER=$(whoami); echo USER=${USER} """)
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to export USER: {str(obs)}')

    # inject the init script
    script_dir = os.path.dirname(__file__)

    # inject the instance info
    action = CmdRunAction(command='mkdir -p /swe_util/eval_data/instances')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to create /swe_util/eval_data/instances: {str(obs)}',
    )

    swe_instance_json_name = 'swe-bench-instance.json'
    with tempfile.TemporaryDirectory() as temp_dir:
        # Construct the full path for the desired file name within the temporary directory
        temp_file_path = os.path.join(temp_dir, swe_instance_json_name)
        # Write to the file with the desired name within the temporary directory
        with open(temp_file_path, 'w') as f:
            if not isinstance(instance, dict):
                json.dump([instance.to_dict()], f)
            else:
                json.dump([instance], f)

        # Copy the file to the desired location
        runtime.copy_to(temp_file_path, '/swe_util/eval_data/instances/')

        # inject the instance swe entry
        runtime.copy_to(
            str(os.path.join(script_dir, 'scripts/setup/instance_swe_entry.sh')),
            '/swe_util/',
        )

    action = CmdRunAction(command='cat ~/.bashrc')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to cat ~/.bashrc: {str(obs)}')

    action = CmdRunAction(command='source ~/.bashrc')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    if isinstance(obs, ErrorObservation):
        logger.error(f'Failed to source ~/.bashrc: {str(obs)}')
    assert_and_raise(obs.exit_code == 0, f'Failed to source ~/.bashrc: {str(obs)}')

    action = CmdRunAction(command='source /swe_util/instance_swe_entry.sh')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to source /swe_util/instance_swe_entry.sh: {str(obs)}',
    )

    action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to cd to /workspace/{workspace_dir_name}: {str(obs)}',
    )

    # # HACK: Some containers have uncommitted changes, please add all changes and commit them.
    # action = CmdRunAction(command='git add -A')
    # action.set_hard_timeout(600)
    # logger.info(action, extra={'msg_type': 'ACTION'})
    # obs = runtime.run_action(action)
    # logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    # # assert_and_raise(obs.exit_code == 0, f'Failed to git add -A: {str(obs)}')

    # action = CmdRunAction(command='git commit -m "Fix environment"')
    # action.set_hard_timeout(600)
    # logger.info(action, extra={'msg_type': 'ACTION'})
    # obs = runtime.run_action(action)
    # logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    # # assert_and_raise(
    # #     obs.exit_code == 0,
    # #     f'Failed to git commit -m "Fix environment": {str(obs)}',
    # # )

    action = CmdRunAction(command='git reset --hard')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to git reset --hard: {str(obs)}')

    action = CmdRunAction(
        command='for remote_name in $(git remote); do git remote remove "${remote_name}"; done'
    )
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to remove git remotes: {str(obs)}')

    action = CmdRunAction(command='which python')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0 and 'testbed' in obs.content,
        f'Expected to find python interpreter from testbed, but got: {str(obs)}',
    )

    logger.info('-' * 30)
    logger.info('END Runtime Initialization Fn')
    logger.info('-' * 30)


def complete_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required, but it is used to get the workspace_dir_name
) -> dict[str, Any]:
    """Complete the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    If you need to do something in the sandbox to get the correctness metric after
    the agent has run, modify this function.
    """
    logger.info('-' * 30)
    logger.info('BEGIN Runtime Completion Fn')
    logger.info('-' * 30)
    obs: CmdOutputObservation
    workspace_dir_name = _get_swebench_workspace_dir_name(instance)

    action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    if obs.exit_code == -1:
        # The previous command is still running
        # We need to kill previous command
        logger.info('The previous command is still running, trying to kill it...')
        action = CmdRunAction(command='C-c')
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Then run the command again
        action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
        action.set_hard_timeout(600)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    if obs.exit_code == -1:
        # The previous command is still running
        # We need to kill previous command
        logger.info('The previous command is still running, trying to ctrl+z it...')
        action = CmdRunAction(command='C-z')
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Then run the command again
        action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
        action.set_hard_timeout(600)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to cd to /workspace/{workspace_dir_name}: {str(obs)}',
    )

    action = CmdRunAction(command='git config --global core.pager ""')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to git config --global core.pager "": {str(obs)}',
    )

    # First check for any git repositories in subdirectories
    action = CmdRunAction(command='find . -type d -name .git -not -path "./.git"')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to find git repositories: {str(obs)}',
    )

    git_dirs = [p for p in obs.content.strip().split('\n') if p]
    if git_dirs:
        # Remove all .git directories in subdirectories
        for git_dir in git_dirs:
            action = CmdRunAction(command=f'rm -rf "{git_dir}"')
            action.set_hard_timeout(600)
            logger.info(action, extra={'msg_type': 'ACTION'})
            obs = runtime.run_action(action)
            logger.info(obs, extra={'msg_type': 'OBSERVATION'})
            assert_and_raise(
                isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
                f'Failed to remove git directory {git_dir}: {str(obs)}',
            )

    # add all files
    action = CmdRunAction(command='git add -A')
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to git add -A: {str(obs)}',
    )

    # Remove binary files from git staging
    action = CmdRunAction(command=remove_binary_files_from_git())
    action.set_hard_timeout(600)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to remove binary files: {str(obs)}',
    )

    n_retries = 0
    git_patch = None
    while n_retries < 5:
        action = CmdRunAction(
            command=f'git diff --no-color --cached {instance["base_commit"]} > patch.diff'
        )
        action.set_hard_timeout(max(300 + 100 * n_retries, 600))
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        n_retries += 1
        if isinstance(obs, CmdOutputObservation):
            if obs.exit_code == 0:
                # Read the patch file
                action = FileReadAction(path='patch.diff')
                action.set_hard_timeout(max(300 + 100 * n_retries, 600))
                logger.info(action, extra={'msg_type': 'ACTION'})
                obs = runtime.run_action(action)
                logger.info(obs, extra={'msg_type': 'OBSERVATION'})
                if isinstance(obs, FileReadObservation):
                    git_patch = obs.content
                    break
                elif isinstance(obs, ErrorObservation):
                    # Fall back to cat "patch.diff" to get the patch
                    assert 'File could not be decoded as utf-8' in obs.content
                    action = CmdRunAction(command='cat patch.diff')
                    action.set_hard_timeout(max(300 + 100 * n_retries, 600))
                    logger.info(action, extra={'msg_type': 'ACTION'})
                    obs = runtime.run_action(action)
                    assert isinstance(obs, CmdOutputObservation) and obs.exit_code == 0
                    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
                    git_patch = obs.content
                    break
                else:
                    assert_and_raise(False, f'Unexpected observation type: {str(obs)}')
            else:
                logger.info('Failed to get git diff, retrying...')
                sleep_if_should_continue(10)
        elif isinstance(obs, ErrorObservation):
            logger.error(f'Error occurred: {obs.content}. Retrying...')
            sleep_if_should_continue(10)
        else:
            assert_and_raise(False, f'Unexpected observation type: {str(obs)}')

    assert_and_raise(git_patch is not None, 'Failed to get git diff (None)')

    # Remove binary diffs from the patch
    git_patch = remove_binary_diffs(git_patch)

    logger.info('-' * 30)
    logger.info('END Runtime Completion Fn')
    logger.info('-' * 30)
    return {'git_patch': git_patch}

class CPUGroupManager:
    def __init__(self, cpu_groups_queue: multiprocessing.Queue):
        self.cpu_groups_queue = cpu_groups_queue

    def __enter__(self):
        # Get the current CPU group for this worker]
        if self.cpu_groups_queue is not None:
            self.cpu_group = self.cpu_groups_queue.get()
            logger.info(f'Worker started with CPU group: {self.cpu_group}')
            return self.cpu_group
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        # Put the CPU group back into the queue for other workers to use
        if self.cpu_groups_queue is not None:
            self.cpu_groups_queue.put(self.cpu_group)
            logger.info(f'Worker finished with CPU group: {self.cpu_group}')


def cleanup_docker_resources_for_worker():
    """Clean up Docker resources specific to this worker process.

    This prevents cascade failures when one worker's container crashes.
    Note: This only cleans up stale locks, not containers, to avoid
    interfering with other workers. Container cleanup is handled
    by the DockerRuntime.close() method based on configuration.
    """
    import os
    import tempfile

    # Clean up any stale port locks from crashed processes
    try:
        from openhands.runtime.utils.port_lock import cleanup_stale_locks
        cleanup_stale_locks(max_age_seconds=300)  # Clean up locks older than 5 minutes
    except Exception as e:
        logger.debug(f'Error cleaning up stale port locks: {e}')


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
    runtime_failure_count: int = 0,
    cpu_groups_queue: multiprocessing.Queue = None,
) -> EvalOutput:
    # Clean up any Docker resources from previous failed runs
    cleanup_docker_resources_for_worker()

    # HACK: Use the global and get the cpu group for this worker.
    with CPUGroupManager(cpu_groups_queue) as cpu_group:
        config = get_config(instance, metadata, cpu_group=cpu_group)

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
            reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
        else:
            logger.info(f'Starting evaluation for instance {instance.instance_id}.')

        # Increase resource_factor with increasing attempt_id
        # if runtime_failure_count > 0:
        #     config.sandbox.remote_runtime_resource_factor = min(
        #         config.sandbox.remote_runtime_resource_factor * (2**runtime_failure_count),
        #         8,
        #     )
        #     logger.warning(
        #         f'This is the {runtime_failure_count + 1}th attempt for instance {instance.instance_id}, setting resource factor to {config.sandbox.remote_runtime_resource_factor}'
        #     )

        metadata = copy.deepcopy(metadata)
        metadata.details['runtime_failure_count'] = runtime_failure_count
        metadata.details['remote_runtime_resource_factor'] = (
            config.sandbox.remote_runtime_resource_factor
        )

        runtime = create_runtime(config, sid=None)
        call_async_from_sync(runtime.connect)

        try:
            initialize_runtime(runtime, instance, metadata)

            message_action = get_instruction(instance, metadata)

            # Here's how you can run the agent (similar to the `main` function) and get the final task state
            state: State | None = asyncio.run(
                run_controller(
                    config=config,
                    initial_user_action=message_action,
                    runtime=runtime,
                    fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                        metadata.agent_class
                    ],
                )
            )

            # if fatal error, throw EvalError to trigger re-run
            if is_fatal_evaluation_error(state.last_error):
                raise EvalException('Fatal error detected: ' + state.last_error)

            # ======= THIS IS SWE-Bench specific =======
            # Get git patch
            return_val = complete_runtime(runtime, instance)
            git_patch = return_val['git_patch']
            logger.info(
                f'Got git diff for instance {instance.instance_id}:\n--------\n{git_patch}\n--------'
            )
        except Exception as e:
            # Log the error but don't let it crash other workers
            logger.error(f'Error in worker processing instance {instance.instance_id}: {str(e)}')
            raise
        finally:
            # Ensure runtime is properly closed to prevent cascade failures
            try:
                runtime.close()
            except Exception as e:
                logger.warning(f'Error closing runtime for {instance.instance_id}: {str(e)}')
                # Don't re-raise - we want to continue cleanup

        # ==========================================

        # ======= Attempt to evaluate the agent's edits =======
        # we use eval_infer.sh to evaluate the agent's edits, not here
        # because the agent may alter the environment / testcases
        test_result = {
            'git_patch': git_patch,
        }

        # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
        # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.
        if state is None:
            raise ValueError('State should not be None.')

        # NOTE: this is NO LONGER the event stream, but an agent history that includes delegate agent's events
        histories = [event_to_dict(event) for event in state.history]
        metrics = get_metrics(state)

        # Save the output
        instruction = message_action.content
        if message_action.image_urls:
            instruction += (
                '\n\n<image_urls>' + '\n'.join(message_action.image_urls) + '</image_urls>'
            )
        output = EvalOutput(
            instance_id=instance.instance_id,
            instruction=instruction,
            instance=instance.to_dict(),  # SWE Bench specific
            test_result=test_result,
            metadata=metadata,
            history=histories,
            metrics=metrics,
            error=state.last_error if state and state.last_error else None,
        )
        return output


def filter_dataset(dataset: pd.DataFrame, filter_column: str) -> pd.DataFrame:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.toml')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = toml.load(file)
            if 'selected_ids' in data:
                selected_ids = data['selected_ids']
                logger.info(
                    f'Filtering {len(selected_ids)} tasks from "selected_ids"...'
                )
                subset = dataset[dataset[filter_column].isin(selected_ids)]
                logger.info(f'Retained {subset.shape[0]} tasks after filtering')
                return subset
            if 'selected_repos' in data:
                # repos for the swe-bench instances:
                # ['astropy/astropy', 'django/django', 'matplotlib/matplotlib', 'mwaskom/seaborn', 'pallets/flask', 'psf/requests', 'pydata/xarray', 'pylint-dev/pylint', 'pytest-dev/pytest', 'scikit-learn/scikit-learn', 'sphinx-doc/sphinx', 'sympy/sympy']
                selected_repos = data['selected_repos']
                if isinstance(selected_repos, str):
                    selected_repos = [selected_repos]
                assert isinstance(selected_repos, list)
                logger.info(
                    f'Filtering {selected_repos} tasks from "selected_repos"...'
                )
                subset = dataset[dataset['repo'].isin(selected_repos)]
                logger.info(f'Retained {subset.shape[0]} tasks after filtering')
                return subset

    skip_ids = os.environ.get('SKIP_IDS', '').split(',')
    if len(skip_ids) > 0:
        logger.info(f'Filtering {len(skip_ids)} tasks from "SKIP_IDS"...')
        return dataset[~dataset[filter_column].isin(skip_ids)]
    return dataset


def divide_cpus_among_workers(num_workers, num_cpus_per_worker=4, num_to_skip=0):
    """Divide CPUs among workers, with better error handling for multiprocessing."""
    try:
        current_cpus = list(os.sched_getaffinity(0))
    except AttributeError:
        # os.sched_getaffinity not available on all platforms
        import multiprocessing
        current_cpus = list(range(multiprocessing.cpu_count()))

    num_cpus = len(current_cpus)
    if num_workers <= 0:
        raise ValueError("Number of workers must be greater than 0")

    # Chec that num worers and num_cpus_per_worker fit into available CPUs
    total_cpus_needed = num_workers * num_cpus_per_worker + num_to_skip
    if total_cpus_needed > num_cpus:
        raise ValueError(
            f"Not enough CPUs available. Requested {total_cpus_needed} "
            f"CPUs (num_workers={num_workers}, num_cpus_per_worker={num_cpus_per_worker}, "
            f"num_to_skip={num_to_skip}), but only {num_cpus} CPUs are available."
        )

    # Divide this into groups, skipping the first `num_to_skip` CPUs.
    available_cpus = current_cpus[num_to_skip:]
    cpu_groups = [
        available_cpus[i * num_cpus_per_worker : (i + 1) * num_cpus_per_worker]
        for i in range(num_workers)
    ]
    print(f"Divided {num_cpus} CPUs into {num_workers} groups, each with {num_cpus_per_worker} CPUs.")
    print(f"CPU groups: {cpu_groups}")

    return cpu_groups



if __name__ == '__main__':
    parser = get_evaluation_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        default=None,
        help='data set to evaluate on, for now use local.',
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        help='split to evaluate on',
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='swe',
        help='mode to evaluate on',
    )

    args, _ = parser.parse_known_args()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenHands's repo

    # dataset = load_dataset(args.dataset, split=args.split)
    # swe_bench_tests = filter_dataset(dataset.to_pandas(), 'instance_id')
    dataset = load_dataset(args.dataset, split=args.split)


    # Convert dataset to pandas DataFrame if it is not already.
    if not isinstance(dataset, pd.DataFrame):
        dataset = dataset.to_pandas()

    dataset['version'] = dataset['version'].astype(str)

    # Convert created_at column to string.
    dataset['created_at'] = dataset['created_at'].astype(str)

    swe_bench_tests = filter_dataset(dataset, 'instance_id')

    logger.info(
        f'Loaded dataset {args.dataset} with split {args.split}: {len(swe_bench_tests)} tasks'
    )

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        llm_config.log_completions = True
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    # Get condenser config from environment variable
    condenser_name = os.environ.get('EVAL_CONDENSER')
    if condenser_name:
        condenser_config = get_condenser_config_arg(condenser_name)
        if condenser_config is None:
            raise ValueError(
                f'Could not find Condenser config: EVAL_CONDENSER={condenser_name}'
            )
    else:
        # If no specific condenser config is provided via env var, default to NoOpCondenser
        condenser_config = NoOpCondenserConfig()
        logger.debug(
            'No Condenser config provided via EVAL_CONDENSER, using NoOpCondenser.'
        )

    details = {'mode': args.mode}
    _agent_cls = openhands.agenthub.Agent.get_cls(args.agent_cls)

    dataset_descrption = (
        args.dataset.replace('/', '__') + '-' + args.split.replace('/', '__')
    )
    metadata = make_metadata(
        llm_config,
        dataset_descrption,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
        details=details,
        condenser_config=condenser_config,
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    print(f'### OUTPUT FILE: {output_file} ###')

    # Run evaluation in iterative mode:
    # If a rollout fails to output AgentFinishAction, we will try again until it succeeds OR total 3 attempts have been made.
    ITERATIVE_EVAL_MODE = (
        os.environ.get('ITERATIVE_EVAL_MODE', 'false').lower() == 'true'
    )
    ITERATIVE_EVAL_MODE_MAX_ATTEMPTS = int(
        os.environ.get('ITERATIVE_EVAL_MODE_MAX_ATTEMPTS', '3')
    )

    # Get all CPUs and divide into groups of num_workers and put them into a multiprocessing.Queue.
    cpu_groups_queue = None
    cpu_groups_list = divide_cpus_among_workers(args.eval_num_workers, num_to_skip=8)
    cpu_groups_queue = multiprocessing.Manager().Queue()
    for cpu_group in cpu_groups_list:
        cpu_groups_queue.put(cpu_group)

    if not ITERATIVE_EVAL_MODE:
        # load the dataset
        instances = prepare_dataset(swe_bench_tests, output_file, args.eval_n_limit)

        # # DEEPSEEK:
        # INSTANCES_ALREADY_RUN = set([
        #     "scikit-learn__scikit-learn-24856","pandas-dev__pandas-26721","numpy__numpy-21354","pandas-dev__pandas-53013","pandas-dev__pandas-30747","pandas-dev__pandas-37945","pandas-dev__pandas-33540","pandas-dev__pandas-52054","pandas-dev__pandas-43694","scipy__scipy-13107","pandas-dev__pandas-53088","astropy__astropy-12701","pandas-dev__pandas-45242","scikit-learn__scikit-learn-28064","pandas-dev__pandas-24308","pandas-dev__pandas-48504","pandas-dev__pandas-27669","pandas-dev__pandas-34199","pandas-dev__pandas-38353","pandas-dev__pandas-43353","pandas-dev__pandas-45247","scipy__scipy-10921","pandas-dev__pandas-36325","pandas-dev__pandas-49851","pandas-dev__pandas-48472","scipy__scipy-14625","dask__dask-6293","pandas-dev__pandas-26702","pandas-dev__pandas-43281","scikit-learn__scikit-learn-22106","pydata__xarray-7382","pandas-dev__pandas-43634","pandas-dev__pandas-46235","pandas-dev__pandas-42631","matplotlib__matplotlib-14504","pandas-dev__pandas-44943","numpy__numpy-24610","pandas-dev__pandas-43725","pandas-dev__pandas-31300","matplotlib__matplotlib-26164","pandas-dev__pandas-38148","pandas-dev__pandas-43010","dask__dask-6491","pandas-dev__pandas-57855","pandas-dev__pandas-41567","pandas-dev__pandas-54835","pandas-dev__pandas-59647","pandas-dev__pandas-52548","astropy__astropy-7643","pandas-dev__pandas-43237","astropy__astropy-7649","pandas-dev__pandas-56508","matplotlib__matplotlib-19760","astropy__astropy-7549","dask__dask-7403","numpy__numpy-12321","pandas-dev__pandas-37971","matplotlib__matplotlib-17994","pandas-dev__pandas-43308","pydata__xarray-7374","scikit-learn__scikit-learn-15834","matplotlib__matplotlib-29399","pandas-dev__pandas-44908","pandas-dev__pandas-56110","pydata__xarray-7824","pandas-dev__pandas-40840","pandas-dev__pandas-51518","numpy__numpy-19601","pandas-dev__pandas-55515","pydata__xarray-9808","pandas-dev__pandas-51784","pydata__xarray-9429","astropy__astropy-16813","pandas-dev__pandas-43510","pandas-dev__pandas-24023","pandas-dev__pandas-44857","matplotlib__matplotlib-17177","astropy__astropy-12699","scipy__scipy-11478","scipy__scipy-10564","numpy__numpy-25788","pandas-dev__pandas-32883","pandas-dev__pandas-42714","pandas-dev__pandas-56841","scikit-learn__scikit-learn-13290","scipy__scipy-10393","pandas-dev__pandas-56128","pandas-dev__pandas-36872","pandas-dev__pandas-49577","scipy__scipy-13611","pandas-dev__pandas-38379","scipy__scipy-16599","astropy__astropy-17004","pandas-dev__pandas-26015","dask__dask-7104","pandas-dev__pandas-36638","pandas-dev__pandas-48338","pandas-dev__pandas-43578","pandas-dev__pandas-25953","pandas-dev__pandas-40072","scipy__scipy-10477","pandas-dev__pandas-53731","dask__dask-5501","dask__dask-10428","scikit-learn__scikit-learn-25713","pandas-dev__pandas-24491","pandas-dev__pandas-42197","pandas-dev__pandas-56061","pandas-dev__pandas-42704","scikit-learn__scikit-learn-15615","scipy__scipy-10939","pandas-dev__pandas-44758","pandas-dev__pandas-37064","matplotlib__matplotlib-26899","matplotlib__matplotlib-18756","pandas-dev__pandas-43696","pandas-dev__pandas-46040","pandas-dev__pandas-44192","pandas-dev__pandas-34192","pandas-dev__pandas-46330","pandas-dev__pandas-23888","pandas-dev__pandas-40254","numpy__numpy-13250","pandas-dev__pandas-52672","pandas-dev__pandas-29134","astropy__astropy-6940","numpy__numpy-25299","numpy__numpy-18324","pandas-dev__pandas-41911","pandas-dev__pandas-36317","scikit-learn__scikit-learn-22206","matplotlib__matplotlib-13917","pandas-dev__pandas-56919","pandas-dev__pandas-37118","numpy__numpy-11720","pandas-dev__pandas-30768","dask__dask-7023","pandas-dev__pandas-49772","pandas-dev__pandas-34948","pandas-dev__pandas-33032","pandas-dev__pandas-25070","astropy__astropy-16670","astropy__astropy-13471","astropy__astropy-8998","scikit-learn__scikit-learn-17737","pandas-dev__pandas-43683","numpy__numpy-18203","matplotlib__matplotlib-22108","pandas-dev__pandas-47234","pandas-dev__pandas-44594","pandas-dev__pandas-43823","numpy__numpy-19620","scikit-learn__scikit-learn-25490","pandas-dev__pandas-29820","pandas-dev__pandas-57560","dask__dask-5890","pandas-dev__pandas-40035","pandas-dev__pandas-55898","pandas-dev__pandas-31037","astropy__astropy-16222","pandas-dev__pandas-39664","dask__dask-6186","numpy__numpy-13697","pandas-dev__pandas-39388","scikit-learn__scikit-learn-13310","pandas-dev__pandas-44666","dask__dask-5933","pandas-dev__pandas-44832","pandas-dev__pandas-46109","pandas-dev__pandas-24083","pandas-dev__pandas-43171","pandas-dev__pandas-57812","scipy__scipy-12001","pandas-dev__pandas-43059","pydata__xarray-9001","pandas-dev__pandas-34052","astropy__astropy-8502","matplotlib__matplotlib-23287","pandas-dev__pandas-59608","pandas-dev__pandas-42611","astropy__astropy-13899","pandas-dev__pandas-30797","dask__dask-5553","pandas-dev__pandas-42998","matplotlib__matplotlib-22875","matplotlib__matplotlib-23759","pandas-dev__pandas-27448","pandas-dev__pandas-51344","numpy__numpy-21832","pandas-dev__pandas-43274","astropy__astropy-7616","pandas-dev__pandas-40178","pandas-dev__pandas-32826","pydata__xarray-7735","scipy__scipy-11982","astropy__astropy-17425","astropy__astropy-6941","pandas-dev__pandas-25820","pandas-dev__pandas-43354","pandas-dev__pandas-41972","matplotlib__matplotlib-15834","pandas-dev__pandas-55839","pandas-dev__pandas-52145","pandas-dev__pandas-43558","scikit-learn__scikit-learn-23149","astropy__astropy-13497","pandas-dev__pandas-34737","pandas-dev__pandas-57034","pandas-dev__pandas-39332","scipy__scipy-13566","numpy__numpy-19608","pandas-dev__pandas-32825","numpy__numpy-21394","matplotlib__matplotlib-17995","astropy__astropy-7924","numpy__numpy-19609","astropy__astropy-16742","pandas-dev__pandas-52430","pydata__xarray-7472","astropy__astropy-16243","pandas-dev__pandas-53231","pandas-dev__pandas-27495","pandas-dev__pandas-26711","pandas-dev__pandas-43277","astropy__astropy-8428","matplotlib__matplotlib-26198","scikit-learn__scikit-learn-27344","pandas-dev__pandas-43073","pandas-dev__pandas-42268","scikit-learn__scikit-learn-15049","astropy__astropy-13898","astropy__astropy-16096","pandas-dev__pandas-26391","dask__dask-10356","pandas-dev__pandas-26605","pandas-dev__pandas-55131","pandas-dev__pandas-43332","pandas-dev__pandas-37569","astropy__astropy-15900","pandas-dev__pandas-42353","astropy__astropy-8349","dask__dask-5891","pydata__xarray-7796","scipy__scipy-10467","numpy__numpy-19599","numpy__numpy-24663","scikit-learn__scikit-learn-21837","pandas-dev__pandas-25665","scikit-learn__scikit-learn-17235","scikit-learn__scikit-learn-9843","pandas-dev__pandas-36432","pandas-dev__pandas-33324","pandas-dev__pandas-53955","pandas-dev__pandas-43524","pandas-dev__pandas-46349","scipy__scipy-10064","pandas-dev__pandas-56089","astropy__astropy-7422","pandas-dev__pandas-44566","pandas-dev__pandas-56806","numpy__numpy-26599","scipy__scipy-11757","scikit-learn__scikit-learn-10610","scikit-learn__scikit-learn-25186","astropy__astropy-16673","pandas-dev__pandas-34354","numpy__numpy-27830","pandas-dev__pandas-30171","astropy__astropy-16088","dask__dask-11625","pandas-dev__pandas-43285","pandas-dev__pandas-43760","scikit-learn__scikit-learn-15257","pandas-dev__pandas-57459","pandas-dev__pandas-48976","pandas-dev__pandas-51339","pandas-dev__pandas-52928","pandas-dev__pandas-60121","pandas-dev__pandas-57534","scikit-learn__scikit-learn-22235","pandas-dev__pandas-32856","pandas-dev__pandas-42486","pandas-dev__pandas-26776","dask__dask-7172","matplotlib__matplotlib-18018","pydata__xarray-4740","pandas-dev__pandas-50310","pandas-dev__pandas-55736","pandas-dev__pandas-55084","scipy__scipy-12474","pandas-dev__pandas-43160","pandas-dev__pandas-51592","astropy__astropy-8494","astropy__astropy-17461","pandas-dev__pandas-26697","pandas-dev__pandas-56997","pandas-dev__pandas-46107","pandas-dev__pandas-52836","pandas-dev__pandas-32821","dask__dask-10922","pandas-dev__pandas-53806","astropy__astropy-16295","pandas-dev__pandas-56062","pandas-dev__pandas-34178","pandas-dev__pandas-29469","dask__dask-6669","numpy__numpy-12575","scikit-learn__scikit-learn-17878","scikit-learn__scikit-learn-29060","pandas-dev__pandas-38560","pandas-dev__pandas-52685","pandas-dev__pandas-48611","pandas-dev__pandas-48502","pandas-dev__pandas-56345","scikit-learn__scikit-learn-29835","pandas-dev__pandas-48609","pandas-dev__pandas-37426","pandas-dev__pandas-40339","pandas-dev__pandas-42270","astropy__astropy-17043","scipy__scipy-12587","pandas-dev__pandas-43243","scipy__scipy-11358","pandas-dev__pandas-39972","pandas-dev__pandas-35166","pandas-dev__pandas-37450","pydata__xarray-5661","pandas-dev__pandas-38103","numpy__numpy-19618","pandas-dev__pandas-52111","pandas-dev__pandas-44610","dask__dask-5940","pandas-dev__pandas-37149","pandas-dev__pandas-37130","matplotlib__matplotlib-21564","scikit-learn__scikit-learn-19606","pandas-dev__pandas-32130","matplotlib__matplotlib-15346","pandas-dev__pandas-43335","pandas-dev__pandas-45708","pandas-dev__pandas-61014","pandas-dev__pandas-43352","pandas-dev__pandas-45854","pandas-dev__pandas-26773","pandas-dev__pandas-36280","pandas-dev__pandas-44827","pandas-dev__pandas-49596","pandas-dev__pandas-45931","matplotlib__matplotlib-19564","pandas-dev__pandas-43589","astropy__astropy-7010","pandas-dev__pandas-31409","dask__dask-5884","pandas-dev__pandas-27384","numpy__numpy-12596","pandas-dev__pandas-58992","pandas-dev__pandas-43370","pandas-dev__pandas-41924"
        # ])

        # print(instances[:5])

        # # remove from dataframe.
        # instances = instances[~instances["instance_id"].isin(INSTANCES_ALREADY_RUN)]

        # print(f"### DEEPSEEK: After removing already run instances, {len(instances)} instances remain to run. ###")

        # TODO: Add judging later?
        # if len(instances) > 0 and not isinstance(
        #     instances['PASS_TO_PASS'][instances['PASS_TO_PASS'].index[0]], str
        # ):
        #     for col in ['PASS_TO_PASS', 'FAIL_TO_PASS']:
        #         instances[col] = instances[col].apply(lambda x: str(x))

        process_instance_with_cpu_groups = functools.partial(
            process_instance,
            cpu_groups_queue=cpu_groups_queue,
        )

        config = get_config(
            instances.iloc[0],  # Use the first instance to get the config
            metadata,
            cpu_group=None,  # We will use the cpu_groups_queue to get the cpu group later
        )

        run_evaluation(
            instances,
            metadata,
            output_file,
            args.eval_num_workers,
            process_instance_with_cpu_groups,
            timeout_seconds=8
            * 60
            * 60,  # 8 hour PER instance should be more than enough
            max_retries=3,
        )
    else:
        critic = AgentFinishedCritic()

        def get_cur_output_file_path(attempt: int) -> str:
            return (
                f'{output_file.removesuffix(".jsonl")}.critic_attempt_{attempt}.jsonl'
            )

        eval_ids = None
        for attempt in range(1, ITERATIVE_EVAL_MODE_MAX_ATTEMPTS + 1):
            cur_output_file = get_cur_output_file_path(attempt)
            logger.info(
                f'Running evaluation with critic {critic.__class__.__name__} for attempt {attempt} of {ITERATIVE_EVAL_MODE_MAX_ATTEMPTS}.'
            )

            # For deterministic eval, we set temperature to 0.1 for (>1) attempt
            # so hopefully we get slightly different results
            if attempt > 1 and metadata.llm_config.temperature == 0:
                logger.info(
                    f'Detected temperature is 0 for (>1) attempt {attempt}. Setting temperature to 0.1...'
                )
                metadata.llm_config.temperature = 0.1

            # Load instances - at first attempt, we evaluate all instances
            # On subsequent attempts, we only evaluate the instances that failed the previous attempt determined by critic
            instances = prepare_dataset(
                swe_bench_tests, cur_output_file, args.eval_n_limit, eval_ids=eval_ids
            )
            if len(instances) > 0 and not isinstance(
                instances['PASS_TO_PASS'][instances['PASS_TO_PASS'].index[0]], str
            ):
                for col in ['PASS_TO_PASS', 'FAIL_TO_PASS']:
                    instances[col] = instances[col].apply(lambda x: str(x))

            # Run evaluation - but save them to cur_output_file
            logger.info(
                f'Evaluating {len(instances)} instances for attempt {attempt}...'
            )
            run_evaluation(
                instances,
                metadata,
                cur_output_file,
                args.eval_num_workers,
                process_instance,
                timeout_seconds=8
                * 60
                * 60,  # 8 hour PER instance should be more than enough
                max_retries=1,
            )

            # When eval is done, we update eval_ids to the instances that failed the current attempt
            instances_failed = []
            logger.info(
                f'Use critic {critic.__class__.__name__} to check {len(instances)} instances for attempt {attempt}...'
            )
            with open(cur_output_file, 'r') as f:
                for line in f:
                    instance = json.loads(line)
                    try:
                        history = [
                            event_from_dict(event) for event in instance['history']
                        ]
                        critic_result = critic.evaluate(
                            history, instance['test_result'].get('git_patch', '')
                        )
                        if not critic_result.success:
                            instances_failed.append(instance['instance_id'])
                    except Exception as e:
                        logger.error(
                            f'Error loading history for instance {instance["instance_id"]}: {e}'
                        )
                        instances_failed.append(instance['instance_id'])
            logger.info(
                f'{len(instances_failed)} instances failed the current attempt {attempt}: {instances_failed}'
            )
            eval_ids = instances_failed

            # If no instances failed, we break
            if len(instances_failed) == 0:
                break

        # Then we should aggregate the results from all attempts into the original output file
        # and remove the intermediate files
        logger.info(
            'Aggregating results from all attempts into the original output file...'
        )
        fout = open(output_file, 'w')
        added_instance_ids = set()
        for attempt in reversed(range(1, ITERATIVE_EVAL_MODE_MAX_ATTEMPTS + 1)):
            cur_output_file = get_cur_output_file_path(attempt)
            if not os.path.exists(cur_output_file):
                logger.warning(
                    f'Intermediate output file {cur_output_file} does not exist. Skipping...'
                )
                continue

            with open(cur_output_file, 'r') as f:
                for line in f:
                    instance = json.loads(line)
                    # Also make sure git_patch is not empty - otherwise we fall back to previous attempt (empty patch is worse than anything else)
                    if (
                        instance['instance_id'] not in added_instance_ids
                        and instance['test_result'].get('git_patch', '').strip()
                    ):
                        fout.write(line)
                        added_instance_ids.add(instance['instance_id'])
            logger.info(
                f'Aggregated instances from {cur_output_file}. Total instances added so far: {len(added_instance_ids)}'
            )
        fout.close()
        logger.info(
            f'Done! Total {len(added_instance_ids)} instances added to {output_file}'
        )
