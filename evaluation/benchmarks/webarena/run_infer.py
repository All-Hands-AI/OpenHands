import asyncio
import json
import os
from typing import Any

try:
    import browsergym.webarena  # noqa F401 register webarena tasks as gym environments
except ModuleNotFoundError:
    # webarena package will be installed in the sandbox runtime; safe to proceed
    pass
import gymnasium as gym
import pandas as pd

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    compatibility_for_eval_history_pairs,
    get_default_sandbox_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
    update_llm_config_for_completions_logging,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    OpenHandsConfig,
    get_llm_config_arg,
    get_evaluation_parser,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import (
    BrowseInteractiveAction,
    CmdRunAction,
    MessageAction,
)
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.runtime.browser.browser_env import (
    BROWSER_EVAL_GET_GOAL_ACTION,
    BROWSER_EVAL_GET_REWARDS_ACTION,
)
from openhands.utils.async_utils import call_async_from_sync

SUPPORTED_AGENT_CLS = {'BrowsingAgent'}


def get_config(
    metadata: EvalMetadata,
    env_id: str,
) -> OpenHandsConfig:
    base_url = os.environ.get('WEBARENA_BASE_URL', None)
    # Allow OPENAI_API_KEY from env or from LLM config
    openai_api_key = os.environ.get('OPENAI_API_KEY', None)
    assert base_url is not None, 'WEBARENA_BASE_URL must be set'
    if not openai_api_key and metadata.llm_config and metadata.llm_config.api_key:
        try:
            openai_api_key = metadata.llm_config.api_key.get_secret_value()
        except Exception:
            pass
    assert openai_api_key, 'OPENAI_API_KEY must be set (env or llm.api_key)'

    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'python:3.12-bookworm'
    sandbox_config.browsergym_eval_env = env_id
    # Ensure evaluation dependencies are installed in runtime image
    sandbox_config.runtime_extra_deps = '/openhands/micromamba/bin/micromamba run -n openhands poetry install --only main,runtime,evaluation --no-interaction --no-root'
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
    # Prefer remote runtime when configured; otherwise use Docker
    runtime_name = (
        'remote' if os.environ.get('SANDBOX_REMOTE_RUNTIME_API_URL') else 'docker'
    )
    if runtime_name == 'docker':
        logger.warning(
            'No SANDBOX_REMOTE_RUNTIME_API_URL provided. Using Docker runtime. '
            'Ensure Docker daemon is available, or set SANDBOX_REMOTE_RUNTIME_API_URL and ALLHANDS_API_KEY to use the remote runtime.'
        )
    config = OpenHandsConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime=runtime_name,
        max_iterations=metadata.max_iterations,
        sandbox=sandbox_config,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(
        update_llm_config_for_completions_logging(
            metadata.llm_config,
            metadata.eval_output_dir,
            env_id,
        )
    )
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.enable_prompt_extensions = False
    return config


def initialize_runtime(
    runtime: Runtime,
) -> dict:
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

    action = BrowseInteractiveAction(browser_actions=BROWSER_EVAL_GET_GOAL_ACTION)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    goal = obs.content

    logger.info(f'{"-" * 50} END Runtime Initialization Fn {"-" * 50}')
    return goal


def complete_runtime(
    runtime: Runtime,
) -> dict[str, Any]:
    """Complete the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    If you need to do something in the sandbox to get the correctness metric after
    the agent has run, modify this function.
    """
    logger.info(f'{"-" * 50} BEGIN Runtime Completion Fn {"-" * 50}')
    obs: CmdOutputObservation

    action = BrowseInteractiveAction(browser_actions=BROWSER_EVAL_GET_REWARDS_ACTION)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    logger.info(f'{"-" * 50} END Runtime Completion Fn {"-" * 50}')
    return {
        'rewards': json.loads(obs.content),
    }


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    env_id = instance.instance_id
    config = get_config(metadata, env_id)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, env_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {env_id}.')

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    task_str = initialize_runtime(runtime)

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=MessageAction(content=task_str),
            runtime=runtime,
        )
    )
    # ======= Attempt to evaluate the agent's environment impact =======

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    metrics = state.metrics.get() if state.metrics else None

    # Instruction is the first message from the USER
    instruction = ''
    for event in state.history:
        if isinstance(event, MessageAction):
            instruction = event.content
            break

    return_val = complete_runtime(runtime)
    logger.info(f'Return value from complete_runtime: {return_val}')
    reward = max(return_val['rewards'])

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=env_id,
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result={
            'reward': reward,
        },
    )
    return output


if __name__ == '__main__':
    parser = get_evaluation_parser()
    args = parser.parse_args()

    dataset = pd.DataFrame(
        {
            'instance_id': [
                id
                for id in gym.envs.registry.keys()
                if id.startswith('browsergym/webarena')
            ]
        }
    )

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
    if llm_config is None:
        # Fallback to the default [llm] config in config.toml
        from openhands.core.config.utils import load_openhands_config

        cfg = load_openhands_config()
        llm_config = cfg.get_llm_config()
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')
    # modify_params must be False for evaluation purpose, for reproducibility and accuracy of results
    llm_config.modify_params = False

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
