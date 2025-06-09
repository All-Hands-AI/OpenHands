"""Bash-related tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox.

Example usage:

```bash
export ALLHANDS_API_KEY="YOUR_API_KEY"
export RUNTIME=remote
export SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.staging.all-hands.dev"
poetry run pytest -vvxss tests/runtime/test_stress_remote_runtime.py
```

"""

import asyncio
import os
import tempfile
import time
from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest
from conftest import TEST_IN_CI

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
)
from openhands.agenthub import Agent
from openhands.controller.state.state import State
from openhands.core.config import (
    AgentConfig,
    LLMConfig,
    OpenHandsConfig,
    SandboxConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import (
    CmdRunAction,
    FileEditAction,
    FileWriteAction,
    MessageAction,
)
from openhands.events.observation import CmdOutputObservation
from openhands.events.serialization.event import event_to_dict
from openhands.llm import LLM
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}


def get_config() -> OpenHandsConfig:
    config = OpenHandsConfig(
        run_as_openhands=False,
        runtime=os.environ.get('RUNTIME', 'remote'),
        sandbox=SandboxConfig(
            base_container_image='python:3.11-bookworm',
            enable_auto_lint=True,
            use_host_network=False,
            # large enough timeout, since some testcases take very long to run
            timeout=300,
            api_key=os.environ.get('ALLHANDS_API_KEY', None),
            remote_runtime_api_url=os.environ.get(
                'SANDBOX_REMOTE_RUNTIME_API_URL', None
            ),
            keep_runtime_alive=False,
            remote_runtime_resource_factor=1,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    agent_config = AgentConfig(
        enable_jupyter=False,
        enable_browsing=False,
        enable_llm_editor=False,
    )
    config.set_agent_config(agent_config)
    return config


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_remote_runtime_eval(n_eval_workers: int = 64):
    """Mimic evaluation setting to test remote runtime in a multi-processing setting."""

    def _initialize_runtime(
        runtime: Runtime,
    ):
        """Initialize the runtime for the agent.

        This function is called before the runtime is used to run the agent.
        """
        logger.info('-' * 30)
        logger.info('BEGIN Runtime Initialization Fn')
        logger.info('-' * 30)
        obs: CmdOutputObservation

        action = CmdRunAction(command="""export USER=$(whoami); echo USER=${USER} """)
        action.set_hard_timeout(600)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert_and_raise(obs.exit_code == 0, f'Failed to export USER: {str(obs)}')

        action = CmdRunAction(command='mkdir -p /dummy_dir')
        action.set_hard_timeout(600)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert_and_raise(
            obs.exit_code == 0,
            f'Failed to create /dummy_dir: {str(obs)}',
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # Construct the full path for the desired file name within the temporary directory
            temp_file_path = os.path.join(temp_dir, 'dummy_file')
            # Write to the file with the desired name within the temporary directory
            with open(temp_file_path, 'w') as f:
                f.write('dummy content')

            # Copy the file to the desired location
            runtime.copy_to(temp_file_path, '/dummy_dir/')

        logger.info('-' * 30)
        logger.info('END Runtime Initialization Fn')
        logger.info('-' * 30)

    def _process_instance(
        instance: pd.Series,
        metadata: EvalMetadata,
        reset_logger: bool = True,
    ) -> EvalOutput:
        config = get_config()

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
            reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
        else:
            logger.info(f'Starting evaluation for instance {instance.instance_id}.')

        runtime = create_runtime(config, headless_mode=True)
        call_async_from_sync(runtime.connect)

        try:
            _initialize_runtime(runtime)

            instruction = 'dummy instruction'
            agent = Agent.get_cls(metadata.agent_class)(
                llm=LLM(config=metadata.llm_config),
                config=config.get_agent_config(metadata.agent_class),
            )

            def next_command(*args, **kwargs):
                return CmdRunAction(command='ls -lah')

            agent.step = MagicMock(side_effect=next_command)

            # Here's how you can run the agent (similar to the `main` function) and get the final task state
            state: State | None = asyncio.run(
                run_controller(
                    config=config,
                    initial_user_action=MessageAction(content=instruction),
                    runtime=runtime,
                    fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                        metadata.agent_class
                    ],
                    agent=agent,
                )
            )

            # if fatal error, throw EvalError to trigger re-run
            if (
                state.last_error
                and 'fatal error during agent execution' in state.last_error
                and 'stuck in a loop' not in state.last_error
            ):
                raise EvalException('Fatal error detected: ' + state.last_error)

        finally:
            runtime.close()

        test_result = {}
        if state is None:
            raise ValueError('State should not be None.')
        histories = [event_to_dict(event) for event in state.history]
        metrics = state.metrics.get() if state.metrics else None

        # Save the output
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

    llm_config = LLMConfig()
    metadata = make_metadata(
        llm_config,
        'dummy_dataset_descrption',
        'CodeActAgent',
        max_iterations=10,
        eval_note='dummy_eval_note',
        eval_output_dir='./dummy_eval_output_dir',
        details={},
    )

    # generate 300 random dummy instances
    dummy_instance = pd.DataFrame(
        {
            'instance_id': [f'dummy_instance_{i}' for i in range(300)],
        }
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(
        dummy_instance, output_file, eval_n_limit=len(dummy_instance)
    )

    run_evaluation(instances, metadata, output_file, n_eval_workers, _process_instance)


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_remote_runtime_long_output_with_soft_and_hard_timeout():
    """Stress test for the remote runtime."""
    config = get_config()

    try:
        runtime = create_runtime(config, headless_mode=True)
        call_async_from_sync(runtime.connect)
        _time_for_test = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Run a command that generates long output multiple times
        for i in range(10):
            start_time = time.time()
            iteration_stats = {
                'iteration': i,
                'timestamp': time.time(),
            }

            # Check overall system memory usage
            mem_action = CmdRunAction(
                'free -k | grep "Mem:" | awk \'{printf "Total: %8.1f MB, Used: %8.1f MB, Free: %8.1f MB, Available: %8.1f MB\\n", $2/1024, $3/1024, $4/1024, $7/1024}\''
            )
            mem_obs = runtime.run_action(mem_action)
            assert mem_obs.exit_code == 0
            logger.info(
                f'System memory usage (iteration {i}): {mem_obs.content.strip()}'
            )
            # Parse memory values from output
            mem_parts = mem_obs.content.strip().split(',')
            for part in mem_parts:
                key, value = part.strip().split(':')
                iteration_stats[f'memory_{key.lower()}'] = float(
                    value.replace('MB', '').strip()
                )

            # Check top memory-consuming processes
            mem_action = CmdRunAction(
                'ps aux | awk \'{printf "%8.1f MB  %s\\n", $6/1024, $0}\' | sort -nr | head -n 5'
            )
            mem_obs = runtime.run_action(mem_action)
            assert mem_obs.exit_code == 0
            _top_processes = [i.strip() for i in mem_obs.content.strip().split('\n')]
            logger.info(
                f'Top 5 memory-consuming processes (iteration {i}):\n{"- " + "\n- ".join(_top_processes)}'
            )
            iteration_stats['top_processes'] = _top_processes

            # Check tmux memory usage (in KB)
            mem_action = CmdRunAction(
                'ps aux | awk \'{printf "%8.1f MB  %s\\n", $6/1024, $0}\' | sort -nr | grep "/usr/bin/tmux" | grep -v grep | awk \'{print $1}\''
            )
            mem_obs = runtime.run_action(mem_action)
            assert mem_obs.exit_code == 0
            logger.info(
                f'Tmux memory usage (iteration {i}): {mem_obs.content.strip()} KB'
            )
            try:
                iteration_stats['tmux_memory_mb'] = float(mem_obs.content.strip())
            except (ValueError, AttributeError):
                iteration_stats['tmux_memory_mb'] = None

            # Check action_execution_server mem
            mem_action = CmdRunAction(
                'ps aux | awk \'{printf "%8.1f MB  %s\\n", $6/1024, $0}\' | sort -nr | grep "action_execution_server" | grep "/openhands/poetry" | grep -v grep | awk \'{print $1}\''
            )
            mem_obs = runtime.run_action(mem_action)
            assert mem_obs.exit_code == 0
            logger.info(
                f'Action execution server memory usage (iteration {i}): {mem_obs.content.strip()} MB'
            )
            try:
                iteration_stats['action_server_memory_mb'] = float(
                    mem_obs.content.strip()
                )
            except (ValueError, AttributeError):
                iteration_stats['action_server_memory_mb'] = None

            # Test soft timeout
            action = CmdRunAction(
                'read -p "Do you want to continue? [Y/n] " answer; if [[ $answer == "Y" ]]; then echo "Proceeding with operation..."; echo "Operation completed successfully!"; else echo "Operation cancelled."; exit 1; fi'
            )
            obs = runtime.run_action(action)
            assert 'Do you want to continue?' in obs.content
            assert obs.exit_code == -1  # Command is still running, waiting for input

            # Send the confirmation
            action = CmdRunAction('Y', is_input=True)
            obs = runtime.run_action(action)
            assert 'Proceeding with operation...' in obs.content
            assert 'Operation completed successfully!' in obs.content
            assert obs.exit_code == 0
            assert '[The command completed with exit code 0.]' in obs.metadata.suffix

            # Test hard timeout w/ long output
            # Generate long output with 1000 asterisks per line
            action = CmdRunAction(
                f'export i={i}; for j in $(seq 1 100); do echo "Line $j - Iteration $i - $(printf \'%1000s\' | tr " " "*")"; sleep 1; done'
            )
            action.set_hard_timeout(2)
            obs = runtime.run_action(action)

            # Verify the output
            assert obs.exit_code == -1
            assert f'Line 1 - Iteration {i}' in obs.content

            # Because hard-timeout is triggered, the terminal will in a weird state
            # where it will not accept any new commands.
            obs = runtime.run_action(CmdRunAction('ls'))
            assert obs.exit_code == -1
            assert 'The previous command is still running' in obs.metadata.suffix

            # We need to send a Ctrl+C to reset the terminal.
            obs = runtime.run_action(CmdRunAction('C-c', is_input=True))
            assert obs.exit_code == 130

            # Now make sure the terminal is in a good state
            obs = runtime.run_action(CmdRunAction('ls'))
            assert obs.exit_code == 0

            duration = time.time() - start_time
            iteration_stats['duration'] = duration
            logger.info(f'Completed iteration {i} in {duration:.2f} seconds')

    finally:
        runtime.close()


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_runtime_memory_limits():
    """Test runtime behavior under resource constraints."""
    config = get_config()

    # For Docker runtime, add resource constraints
    if config.runtime == 'docker':
        config.sandbox.docker_runtime_kwargs = {
            'cpu_period': 100000,  # 100ms
            'cpu_quota': 100000,  # Can use 100ms out of each 100ms period (1 CPU)
            'mem_limit': '4G',  # 4 GB of memory
            'memswap_limit': '0',  # No swap
            'mem_swappiness': 0,  # Disable swapping
            'oom_kill_disable': False,  # Enable OOM killer
        }
    config.sandbox.runtime_startup_env_vars = {
        'RUNTIME_MAX_MEMORY_GB': '3',
        'RUNTIME_MEMORY_MONITOR': 'true',
    }

    try:
        runtime = create_runtime(config, headless_mode=True)
        call_async_from_sync(runtime.connect)

        # Install stress-ng
        action = CmdRunAction(
            command='sudo apt-get update && sudo apt-get install -y stress-ng'
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        action = CmdRunAction(
            command='stress-ng --vm 1 --vm-bytes 6G --timeout 1m --metrics'
        )
        action.set_hard_timeout(120)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'aborted early, out of system resources' in obs.content
        assert obs.exit_code == 3  # OOM killed!

    finally:
        runtime.close()


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_runtime_memory_limits_with_repeated_file_edit():
    """Test runtime behavior under resource constraints with repeated file edits."""
    config = get_config()

    # For Docker runtime, add resource constraints
    if config.runtime == 'docker':
        config.sandbox.docker_runtime_kwargs = {
            'cpu_period': 100000,  # 100ms
            'cpu_quota': 100000,  # Can use 100ms out of each 100ms period (1 CPU)
            'mem_limit': '4G',  # 4 GB of memory
            'memswap_limit': '0',  # No swap
            'mem_swappiness': 0,  # Disable swapping
            'oom_kill_disable': False,  # Enable OOM killer
        }
    config.sandbox.runtime_startup_env_vars = {
        'RUNTIME_MAX_MEMORY_GB': '3',
        'RUNTIME_MEMORY_MONITOR': 'true',
    }

    try:
        runtime = create_runtime(config, headless_mode=True)
        call_async_from_sync(runtime.connect)

        # Create initial test file with base content
        test_file = '/tmp/test_file.txt'
        # base_content = 'content_1\n' * 1000  # Create a reasonably sized file
        base_content = ''
        for i in range(1000):
            base_content += f'content_{i:03d}\n'

        # Use FileWriteAction to create initial file
        write_action = FileWriteAction(path=test_file, content=base_content)
        obs = runtime.run_action(write_action)

        # Perform repeated file edits
        for i in range(1000):
            # Use FileEditAction with str_replace instead of IPythonRunCellAction
            edit_action = FileEditAction(
                command='str_replace',
                path=test_file,
                old_str=f'content_{i:03d}',
                new_str=f'-content_{i:03d}',
            )
            obs = runtime.run_action(edit_action)
            assert f'The file {test_file} has been edited' in obs.content, (
                f'Edit failed at iteration {i}'
            )
            logger.info(f'finished iteration {i}')

        # Verify final file state using FileEditAction view command
        action = FileEditAction(command='view', path=test_file)
        obs = runtime.run_action(action)
        assert '-content_999' in obs.content, 'Final content verification failed'
        logger.info('Final file content verified successfully')

    finally:
        runtime.close()
