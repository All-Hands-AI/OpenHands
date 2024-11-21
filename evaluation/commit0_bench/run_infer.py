import asyncio
import os
from typing import Any

import pandas as pd
from commit0.harness.constants import SPLIT
from datasets import load_dataset

import openhands.agenthub
from evaluation.utils.shared import (
    EvalException,
    EvalMetadata,
    EvalOutput,
    assert_and_raise,
    codeact_user_response,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
    update_llm_config_for_completions_logging,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AgentConfig,
    AppConfig,
    SandboxConfig,
    get_llm_config_arg,
    get_parser,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.events.serialization.event import event_to_dict
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

USE_HINT_TEXT = os.environ.get('USE_HINT_TEXT', 'false').lower() == 'true'
USE_INSTANCE_IMAGE = os.environ.get('USE_INSTANCE_IMAGE', 'false').lower() == 'true'
RUN_WITH_BROWSING = os.environ.get('RUN_WITH_BROWSING', 'false').lower() == 'true'

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'CodeActCommit0Agent': codeact_user_response,
}


def _get_commit0_workspace_dir_name(instance: pd.Series) -> str:
    return f'{instance.repo}'.replace('/', '__')


def get_instruction(instance: pd.Series, metadata: EvalMetadata):
    workspace_dir_name = _get_commit0_workspace_dir_name(instance)
    # Prepare instruction
    if metadata.agent_class == 'CodeActCommit0Agent':
        raise NotImplementedError
        # instruction = (
        #     'We are currently solving the following issue within our repository. Here is the issue text:\n'
        #     '--- BEGIN ISSUE ---\n'
        #     f'{instance.problem_statement}\n'
        #     '--- END ISSUE ---\n\n'
        # )
        # if USE_HINT_TEXT and instance.hints_text:
        #     instruction += (
        #         f'--- BEGIN HINTS ---\n{instance.hints_text}\n--- END HINTS ---\n'
        #     )
        # instruction += CODEACT_SWE_PROMPT.format(workspace_dir_name=workspace_dir_name)
    else:
        # Instruction based on Anthropic's official trajectory
        # https://github.com/eschluntz/swe-bench-experiments/tree/main/evaluation/verified/20241022_tools_claude-3-5-sonnet-updated/trajs
        instruction = (
            '<uploaded_files>\n'
            f'/workspace/{workspace_dir_name}\n'
            '</uploaded_files>\n'
            f"I've uploaded a python code repository in the directory {workspace_dir_name}. Here is your task:\n\n"
            'Here is your task:\n\n'
            '  You need to complete the implementations for all functions (i.e., those with pass\n'
            '  statements) and pass the unit tests.\n\n'
            '  Do not change the names of existing functions or classes, as they may be referenced\n'
            '  from other code like unit tests, etc.\n\n'
            '  When you generate code, you must maintain the original formatting of the function\n'
            '  stubs (such as whitespaces), otherwise we will not able to search/replace blocks\n'
            '  for code modifications, and therefore you will receive a score of 0 for your generated\n'
            '  code.'
            '\n\n'
            'Here is the command to run the unit tests:\n'
            '<test_command>\n'
            f'commit0 test /workspace/{workspace_dir_name} test_ids --branch openhands --commit0-config-file /workspace/.commit0.yaml\n'
            '</test_command>\n\n'
        )

    if RUN_WITH_BROWSING:
        instruction += (
            '<IMPORTANT!>\n'
            'You SHOULD NEVER attempt to browse the web. '
            '</IMPORTANT!>\n'
        )
    return instruction


# TODO: migrate all swe-bench docker to ghcr.io/openhands
DOCKER_IMAGE_PREFIX = os.environ.get(
    'EVAL_DOCKER_IMAGE_PREFIX', 'docker.io/wentingzhao/'
)
logger.info(f'Using docker image prefix: {DOCKER_IMAGE_PREFIX}')


def get_instance_docker_image(instance_id: str) -> str:
    image_name = instance_id.replace('commit-0-', '')
    image_name = image_name.replace(
        '__', '_s_'
    )  # to comply with docker image naming convention
    return (DOCKER_IMAGE_PREFIX.rstrip('/') + '/' + image_name).lower() + ':v0'


def get_config(
    instance: pd.Series,
    metadata: EvalMetadata,
) -> AppConfig:
    # COMMIT0_CONTAINER_IMAGE = 'wentingzhao/'
    assert USE_INSTANCE_IMAGE
    # We use a different instance image for the each instance of commit0 eval
    base_container_image = get_instance_docker_image(instance['instance_id'])
    logger.info(
        f'Using instance container image: {base_container_image}. '
        f'Please make sure this image exists. '
        f'Submit an issue on https://github.com/All-Hands-AI/OpenHands if you run into any issues.'
    )
    # else:
    #     raise
    # base_container_image = SWE_BENCH_CONTAINER_IMAGE
    # logger.info(f'Using swe-bench container image: {base_container_image}')

    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        max_iterations=metadata.max_iterations,
        runtime=os.environ.get('RUNTIME', 'eventstream'),
        sandbox=SandboxConfig(
            base_container_image=base_container_image,
            enable_auto_lint=True,
            use_host_network=False,
            # large enough timeout, since some testcases take very long to run
            timeout=300,
            api_key=os.environ.get('ALLHANDS_API_KEY', None),
            remote_runtime_api_url=os.environ.get('SANDBOX_REMOTE_RUNTIME_API_URL'),
            keep_runtime_alive=False,
            remote_runtime_init_timeout=3600,
        ),
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
        codeact_enable_jupyter=False,
        codeact_enable_browsing=RUN_WITH_BROWSING,
        codeact_enable_llm_editor=False,
    )
    config.set_agent_config(agent_config)
    return config


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info('-' * 30)
    logger.info('BEGIN Runtime Initialization Fn')
    logger.info('-' * 30)
    workspace_dir_name = _get_commit0_workspace_dir_name(instance)
    obs: CmdOutputObservation

    action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to cd to /workspace/{workspace_dir_name}: {str(obs)}',
    )

    action = CmdRunAction(command='git reset --hard')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to git reset --hard: {str(obs)}')

    action = CmdRunAction(
        command='for remote_name in $(git remote); do git remote remove "${remote_name}"; done'
    )
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to remove git remotes: {str(obs)}')

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
    workspace_dir_name = _get_commit0_workspace_dir_name(instance)

    action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to cd to /workspace/{workspace_dir_name}: {str(obs)}',
    )

    action = CmdRunAction(command='git add -A')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to git add -A: {str(obs)}',
    )

    action = CmdRunAction(
        command=f'commit0 evaluate {instance["repo"].split("/")[1]} --branch openhands --commit0-config-file /workspace/.commit0.yaml'
    )
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        isinstance(obs, CmdOutputObservation) and obs.exit_code == 0,
        f'Failed to commit0 evaluate: {str(obs)}',
    )

    return {'eval_result': obs.content.strip()}


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(instance, metadata)
    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    try:
        initialize_runtime(runtime, instance)

        instruction = get_instruction(instance, metadata)

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State | None = asyncio.run(
            run_controller(
                config=config,
                initial_user_action=MessageAction(content=instruction),
                runtime=runtime,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                    metadata.agent_class
                ],
            )
        )

        # if fatal error, throw EvalError to trigger re-run
        if (
            state.last_error
            and 'fatal error during agent execution' in state.last_error
            and 'stuck in a loop' not in state.last_error
        ):
            raise EvalException('Fatal error detected: ' + state.last_error)

        # ======= THIS IS Commit0 specific =======
        # Get git patch
        return_val = complete_runtime(runtime, instance)
        eval_result = return_val['eval_result']
        logger.info(
            f'Got evaluation result for repo {instance.instance_id}:\n--------\n{eval_result}\n--------'
        )
    finally:
        runtime.close()
    # ==========================================

    # ======= Attempt to evaluate the agent's edits =======
    # we use eval_infer.sh to evaluate the agent's edits, not here
    # because the agent may alter the environment / testcases
    test_result = {
        'eval_result': eval_result,
    }

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.
    if state is None:
        raise ValueError('State should not be None.')

    # NOTE: this is NO LONGER the event stream, but an agent history that includes delegate agent's events
    histories = [event_to_dict(event) for event in state.history]
    metrics = state.metrics.get() if state.metrics else None

    # Save the output
    output = EvalOutput(
        instance_id=instance.instance_id,
        instruction=instruction,
        instance=instance.to_dict(),
        test_result=test_result,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
    )
    return output


def commit0_setup(
    dataset: pd.DataFrame, repo_split: str, base_dir: str, commit0_config_file: str
) -> pd.DataFrame:
    """Setup Commit0 dataset based on split type.

    Args:
        dataset: Full Commit0 dataset
        repo_split: Split type ('all', 'lite' or specific repo name)
        base_dir: Base directory of the Commit0 repo
        commit0_config_file: Commit0 config file path

    Returns:
        Filtered dataset based on split type
    """
    # Run commit0 setup command directly

    os.system(
        f'commit0 setup {repo_split} --base-dir {base_dir} --commit0-config-file {commit0_config_file}'
    )

    filtered_dataset = pd.concat(
        [
            dataset[dataset['repo'].str.split('/').str[1] == repo]
            for repo in SPLIT.get(repo_split, [])
        ]
    )

    # Replace all forward slashes in instance_id with hyphens
    filtered_dataset['instance_id'] = filtered_dataset['instance_id'].str.replace(
        '/', '-'
    )

    # Checkout openhands branch for each repo
    for repo in SPLIT.get(repo_split, []):
        repo_path = os.path.join(base_dir, repo)
        if os.path.exists(repo_path):
            logger.info(f'Checking out openhands branch for {repo}')
            os.system(f'cd {repo_path} && git checkout -b openhands')
        else:
            raise ValueError(f'Repo {repo} does not exist in {base_dir}')

    return filtered_dataset


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        default='wentingzhao/commit0_combined',
        help='dataset to evaluate on, only test split exists for this HF dataset',
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        help='this is the HF dataset split',
    )
    parser.add_argument(
        '--repo-split',
        type=str,
        default='lite',
        help='all, lite, or each repo name',
    )
    parser.add_argument(
        '--repo-dir',
        type=str,
        default='repos',
        help='directory to store the repos',
    )
    parser.add_argument(
        '--commit0_file_name',
        type=str,
        default='.commit0.yaml',
        help='commit0 config file name',
    )
    args, _ = parser.parse_known_args()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenHands's repo
    dataset = load_dataset(args.dataset, split=args.split)

    # Setup Commit0
    base_dir = os.path.join(os.path.dirname(__file__), args.repo_dir)
    commit0_config_file = os.path.join(base_dir, args.commit0_file_name)

    commit0_datasets = commit0_setup(
        dataset.to_pandas(), args.repo_split, base_dir, commit0_config_file
    )

    logger.info(f'Loaded dataset {args.dataset} with reposplit {args.repo_split}')

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        llm_config.log_completions = True

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    details = {}
    _agent_cls = openhands.agenthub.Agent.get_cls(args.agent_cls)

    dataset_descrption = (
        args.dataset.replace('/', '__') + '-' + args.repo_split.replace('/', '__')
    )
    metadata = make_metadata(
        llm_config,
        dataset_descrption,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
        details=details,
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')

    instances = prepare_dataset(commit0_datasets, output_file, args.eval_n_limit)

    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        timeout_seconds=120 * 60,  # 2 hour PER instance should be more than enough
    )
