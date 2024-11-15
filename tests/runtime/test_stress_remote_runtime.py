"""Bash-related tests for the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

import asyncio
import os
import tempfile
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
    AppConfig,
    LLMConfig,
    SandboxConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.events.serialization.event import event_to_dict
from openhands.llm import LLM
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    assert (
        os.environ.get('SANDBOX_REMOTE_RUNTIME_API_URL') is not None
    ), 'SANDBOX_REMOTE_RUNTIME_API_URL must be set.'
    assert (
        os.environ.get('ALLHANDS_API_KEY') is not None
    ), 'ALLHANDS_API_KEY must be set.'
    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        max_iterations=metadata.max_iterations,
        runtime='remote',
        sandbox=SandboxConfig(
            base_container_image='python:3.11-bookworm',
            enable_auto_lint=True,
            use_host_network=False,
            # large enough timeout, since some testcases take very long to run
            timeout=300,
            api_key=os.environ.get('ALLHANDS_API_KEY', None),
            remote_runtime_api_url=os.environ.get('SANDBOX_REMOTE_RUNTIME_API_URL'),
            keep_runtime_alive=False,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    agent_config = AgentConfig(
        codeact_enable_jupyter=False,
        codeact_enable_browsing=False,
        codeact_enable_llm_editor=False,
    )
    config.set_agent_config(agent_config)
    return config


def initialize_runtime(
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
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(obs.exit_code == 0, f'Failed to export USER: {str(obs)}')

    action = CmdRunAction(command='mkdir -p /dummy_dir')
    action.timeout = 600
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


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    runtime = create_runtime(config, headless_mode=False)
    call_async_from_sync(runtime.connect)

    try:
        initialize_runtime(runtime)

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


@pytest.mark.skipif(
    TEST_IN_CI,
    reason='This test should only be run locally, not in CI.',
)
def test_stress_remote_runtime(n_eval_workers: int = 64):
    """Mimic evaluation setting to test remote runtime in a multi-processing setting."""

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

    run_evaluation(instances, metadata, output_file, n_eval_workers, process_instance)
