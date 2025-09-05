import asyncio
import os
from typing import Any

import pandas as pd

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    codeact_user_response,
    compatibility_for_eval_history_pairs,
    get_default_sandbox_config_for_eval,
    get_metrics,
    get_openhands_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    OpenHandsConfig,
    get_llm_config_arg,
)
from openhands.core.config.arg_utils import get_evaluation_parser
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import (
    CmdRunAction,
    MessageAction,
)
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

SUPPORTED_AGENT_CLS = {'BrowsingAgent', 'CodeActAgent'}

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'BrowsingAgent': codeact_user_response,
}

# Global variable to store task configs
TASK_CONFIGS = {}


def get_config(
    metadata: EvalMetadata,
    task_config: dict,
) -> OpenHandsConfig:
    base_url = os.environ.get('WEBARENA_BASE_URL', None)
    openai_api_key = os.environ.get('OPENAI_API_KEY', None)
    assert base_url is not None, 'WEBARENA_BASE_URL must be set'
    assert openai_api_key is not None, 'OPENAI_API_KEY must be set'

    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'python:3.12-bookworm'
    # Remove browsergym_eval_env dependency - we'll use regular browser environment
    sandbox_config.runtime_startup_env_vars = {
        'BASE_URL': base_url,
        'OPENAI_API_KEY': openai_api_key,
        'SHOPPING': f'{base_url}:7770/',
        'SHOPPING_ADMIN': f'{base_url}:7780/admin',
        'REDDIT': f'{base_url}:9999',
        'GITLAB': f'{base_url}:8023',
        'WIKIPEDIA': f'{base_url}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing',
        'MAP': f'{base_url}:3000',
        'HOMEPAGE': f'{base_url}:4399',
    }
    config = get_openhands_config_for_eval(
        metadata=metadata,
        runtime='docker',
        sandbox_config=sandbox_config,
        enable_browser=True,
    )
    config.set_llm_config(metadata.llm_config)
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.enable_prompt_extensions = False
    return config


def get_instruction(task_config: dict) -> MessageAction:
    """Create the instruction message for the agent based on the task config."""
    intent = task_config.get('intent', 'Complete the task')
    start_url = task_config.get('start_url', 'about:blank')

    # BrowserGym WebArena already handles URL substitution, so we can use start_url directly
    # Create a comprehensive instruction that includes the task and starting point
    instruction = f"""You are a web browsing agent. Your task is: {intent}

Please start by navigating to: {start_url}

Complete the task by interacting with the webpage as needed. Use the browser tool to navigate, click, fill forms, and perform other web interactions to accomplish the goal."""

    return MessageAction(content=instruction)


def initialize_runtime(
    runtime: Runtime,
    task_config: dict,
) -> None:
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f'{"-" * 50} BEGIN Runtime Initialization Fn {"-" * 50}')
    obs: CmdOutputObservation

    # Set instance id
    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    logger.info(f'{"-" * 50} END Runtime Initialization Fn {"-" * 50}')


def complete_runtime(
    runtime: Runtime,
) -> dict[str, Any]:
    """Complete the runtime for the agent.

    This function is called after the agent has run.
    Since we're using the official webarena evaluation, we don't need to get rewards here.
    """
    logger.info(f'{"-" * 50} BEGIN Runtime Completion Fn {"-" * 50}')

    # Capture the final accessibility tree for WebArena evaluation
    try:
        # Create a browser action to get the current page state with accessibility tree
        from openhands.events.action import BrowseInteractiveAction

        # Use a no-op action that returns the accessibility tree
        final_browse_action = BrowseInteractiveAction(
            browser_actions='noop()',  # No-op action to just get current state
            return_axtree=True,  # Ensure we get the accessibility tree
        )

        # Execute the action to get the final observation with accessibility tree
        final_obs = runtime.browse_interactive(final_browse_action)

        # Extract the accessibility tree from the observation
        final_axtree = None
        if hasattr(final_obs, 'axtree_object') and final_obs.axtree_object:
            final_axtree = final_obs.axtree_object
            logger.info('Successfully captured final accessibility tree')
        else:
            logger.warning('No accessibility tree found in final observation')

        logger.info(f'{"-" * 50} END Runtime Completion Fn {"-" * 50}')
        return {'final_accessibility_tree': final_axtree}

    except Exception as e:
        logger.error(f'Error capturing final accessibility tree: {e}')
        logger.info(f'{"-" * 50} END Runtime Completion Fn {"-" * 50}')
        return {'final_accessibility_tree': None}


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    task_id = instance.instance_id
    task_config = TASK_CONFIGS.get(task_id, {})
    config = get_config(metadata, task_config)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, str(task_id), log_dir)
    else:
        logger.info(f'Starting evaluation for task {task_id}.')

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    initialize_runtime(runtime, task_config)

    # Get the proper instruction message
    message_action = get_instruction(task_config)

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

    if state is None:
        raise ValueError('State should not be None.')

    metrics = get_metrics(state)

    # Instruction is the first message from the USER
    instruction = ''
    for event in state.history:
        if isinstance(event, MessageAction):
            instruction = event.content
            break

    return_val = complete_runtime(runtime)
    logger.info(f'Return value from complete_runtime: {return_val}')

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=str(task_id),
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result={
            'task_config': task_config,  # Store task config for later evaluation
            'final_accessibility_tree': return_val.get('final_accessibility_tree')
            if return_val
            else None,
        },
    )
    return output


if __name__ == '__main__':
    parser = get_evaluation_parser()
    args = parser.parse_args()

    # Set up WebArena environment variables for BrowserGym
    base_url = os.environ.get('WEBARENA_BASE_URL', None)
    if not base_url:
        raise ValueError('WEBARENA_BASE_URL must be set')

    # Set up the WA_ prefixed environment variables that BrowserGym expects
    os.environ['WA_SHOPPING'] = f'{base_url}:7770/'
    os.environ['WA_SHOPPING_ADMIN'] = f'{base_url}:7780/admin'
    os.environ['WA_REDDIT'] = f'{base_url}:9999'
    os.environ['WA_GITLAB'] = f'{base_url}:8023'
    os.environ['WA_WIKIPEDIA'] = (
        f'{base_url}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing'
    )
    os.environ['WA_MAP'] = f'{base_url}:3000'
    os.environ['WA_HOMEPAGE'] = f'{base_url}:4399'

    # Load webarena task configs from BrowserGym
    from browsergym.webarena.config import TASK_IDS
    from browsergym.webarena.task import GenericWebArenaTask

    task_configs = []

    # Load a subset of tasks for testing (first 10 tasks)
    test_task_ids = list(TASK_IDS)[:10]  # Use first 10 tasks for testing

    for task_id in test_task_ids:
        try:
            # Create a temporary task to get the config
            temp_task = GenericWebArenaTask(seed=42, task_id=task_id)

            # Get the first (and likely only) task config for this task_id
            if temp_task.task_configs:
                task_config = temp_task.task_configs[0]
                task_configs.append({'task_id': task_id, 'task_config': task_config})
        except Exception as e:
            print(f'Warning: Could not load task {task_id}: {e}')
            continue

    if not task_configs:
        raise ValueError('No task configs could be loaded from BrowserGym WebArena')

    print(f'Found {len(task_configs)} task configs from BrowserGym WebArena')

    # Store task configs globally for process_instance to access
    for task in task_configs:
        TASK_CONFIGS[str(task['task_id'])] = task['task_config']

    # Create dataset from task configs
    dataset = pd.DataFrame(
        [{'instance_id': str(task['task_id'])} for task in task_configs]
    )

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config, args.config_file)
        # modify_params must be False for evaluation purpose, for reproducibility and accuracy of results
        if llm_config:
            llm_config.modify_params = False
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'webarena',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(dataset, output_file, args.eval_n_limit)

    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
    )
