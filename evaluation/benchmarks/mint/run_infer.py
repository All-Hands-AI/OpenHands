import asyncio
import functools
import os
from typing import Any

import pandas as pd
from datasets import load_dataset

from evaluation.benchmarks.mint.datatypes import TaskState
from evaluation.benchmarks.mint.env import SimplifiedEnv
from evaluation.benchmarks.mint.prompts import ToolPromptTemplate
from evaluation.benchmarks.mint.tasks import Task
from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    compatibility_for_eval_history_pairs,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
    SandboxConfig,
    get_llm_config_arg,
    get_parser,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import (
    Action,
    CmdRunAction,
    MessageAction,
)
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync


def codeact_user_response_mint(state: State, task: Task, task_config: dict[str, int]):
    logger.info(f'Gold reference: {task.reference}')
    logger.info(f'Task config: {task_config}')

    env = SimplifiedEnv(
        agent_state=state,
        task=task,
        task_config=task_config,
    )
    last_action = next(
        (event for event in reversed(state.history) if isinstance(event, Action)),
        None,
    )
    result_state: TaskState = env.step(last_action.message or '')

    state.extra_data['task_state'] = result_state

    if not result_state.latest_output:
        # Task is finished
        msg = '/exit'
    else:
        msg = result_state.latest_output['content']

    logger.info('User response:' + msg)
    return msg


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response_mint,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'IMPORTANT: When your answer is confirmed by the user to be correct, you can use the "finish" tool to finish the interaction.\n'
}

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), 'r') as f:
    MINT_DEPENDENCIES = f.read().splitlines()


def load_incontext_example(task_name: str, with_tool: bool = True):
    assert with_tool, 'NOT with_tool is not supported yet'
    subset = {
        'gsm8k': 'reasoning',
        'math': 'reasoning',
        'mmlu': 'reasoning',
        'theoremqa': 'reasoning',
        'mbpp': 'mbpp',
        'humaneval': 'humaneval',
    }[task_name]
    with open(
        os.path.join(
            os.path.dirname(__file__),
            'tasks',
            'in_context_examples',
            subset,
            'with_tool.txt',
        ),
        'r',
    ) as f:
        return f.read()


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=SandboxConfig(
            base_container_image='xingyaoww/od-eval-mint:v1.0',
            enable_auto_lint=True,
            use_host_network=False,
            runtime_extra_deps=f'$OH_INTERPRETER_PATH -m pip install {" ".join(MINT_DEPENDENCIES)}',
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    return config


def initialize_runtime(runtime: Runtime):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Initialization Fn {'-' * 50}")
    obs: CmdOutputObservation

    # Set instance id
    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command='cd /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    logger.info(f"{'-' * 50} END Runtime Initialization Fn {'-' * 50}")


def process_instance(
    instance: Any,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    config = get_config(metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    # Prepare instruction
    assert metadata.details is not None
    instruction = ToolPromptTemplate(use_tool=True)(
        max_total_steps=metadata.max_iterations,
        max_propose_solution=metadata.details['max_propose_solution'],
        in_context_example=instance.in_context_example,
        task_prompt='Task:\n' + instance.prompt,
    )
    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you or provide the concise RESULT inside <solution> tag AND NEVER ASK FOR HUMAN HELP.\n'

    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[metadata.agent_class]

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    fake_user_response_fn = functools.partial(
        AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[metadata.agent_class],
        task=instance,
        task_config={
            'max_iterations': metadata.max_iterations,
            'max_propose_solution': metadata.details['max_propose_solution'],
        },
    )

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    initialize_runtime(runtime)

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=MessageAction(content=instruction),
            runtime=runtime,
            fake_user_response_fn=fake_user_response_fn,
        )
    )

    if state is None:
        raise ValueError('State should not be None.')

    task_state = None
    if 'task_state' in state.extra_data:
        task_state = state.extra_data['task_state']
        logger.info('Task state: ' + str(task_state.to_dict()))

    metrics = state.metrics.get() if state.metrics else None

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=instance.instance_id,
        instance=instance.to_dict(),
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result={
            'success': task_state.success if task_state else False,
        },
    )
    return output


if __name__ == '__main__':
    parser = get_parser()

    SUBSETS = [
        # Eurus subset: https://arxiv.org/abs/2404.02078
        'math',
        # 'gsm8k',
        'mmlu',
        'theoremqa',
        'mbpp',
        'humaneval',
    ]
    parser.add_argument(
        '--subset',
        default='all',
        choices=SUBSETS + ['all'],
        type=str,
        help='subset of the dataset to be used',
    )
    parser.add_argument(
        '--max-propose-solution',
        default=2,
        type=int,
        help='maximum number of times the agent can propose a solution',
    )

    args, _ = parser.parse_known_args()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenHands's repo
    if args.subset == 'all':
        subsets = SUBSETS
    else:
        subsets = [args.subset]

    dataset_dfs = []
    for subset in subsets:
        in_context_example = load_incontext_example(subset)
        _cur_dataset = load_dataset(
            'ryanhoangt/xingyaoww-mint-bench', name=subset, split='test'
        )
        logger.info(f'Loaded MINT - {subset} subset')
        _df = _cur_dataset.to_pandas().rename(columns={'id': 'instance_id'})
        _df['instance_id'] = _df['instance_id'].apply(lambda x: f'{subset}/{x}')  # noqa
        _df['in_context_example'] = in_context_example
        dataset_dfs.append(_df)
        logger.info(f'Loaded {len(_df)} instances for subset: {subset}')

    dataset_df = pd.concat(dataset_dfs)
    logger.info(f'Loaded {len(dataset_df)} instances for subset: {subsets}')

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        f'MINT-{args.subset}',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
        details={'max_propose_solution': args.max_propose_solution},
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(dataset_df, output_file, args.eval_n_limit)
    run_evaluation(
        instances, metadata, output_file, args.eval_num_workers, process_instance
    )
