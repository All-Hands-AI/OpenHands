import asyncio
import functools
import logging
import os
import pathlib
from typing import Any, Dict

from datasets import load_dataset

from evaluation.swe_bench.swe_env_box import DockerSSHBox
from evaluation.utils.shared import (
    EvalMetadata,
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import get_llm_config_arg, get_parser, load_app_config
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM

from .datatypes import TaskState
from .env import SimplifiedEnv
from .prompts import ToolPromptTemplate
from .tasks import Task

config = load_app_config()


def codeact_user_response_mint(state: State, task: Task, task_config: Dict[str, int]):
    logger.info(f'Gold reference: {task.reference}')
    logger.info(f'Task config: {task_config}')

    env = SimplifiedEnv(
        agent_state=state,
        task=task,
        task_config=task_config,
    )
    last_action = state.history.get_last_action()
    result_state: TaskState = env.step(last_action.message or '')

    state.task_state = result_state

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
    'CodeActAgent': '\nIMPORTANT: When your answer is confirmed by the user to be correct, you can exit using the following command: <execute_bash> exit </execute_bash>.\n'
}


def process_instance(
    instance: Any,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(metadata.llm_config))
    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    # create process-specific workspace dir
    workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            metadata.eval_output_dir, 'logs', f'instance_{instance.task_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance.task_id}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

    logger.info(f'Process-specific workspace mounted at {workspace_mount_path}')

    # use a session id for concurrent processing
    sid = instance.task_id + '_' + str(os.getpid())
    sandbox = DockerSSHBox(
        config=config.sandbox,
        persist_sandbox=False,
        workspace_mount_path=config.workspace_mount_path,
        sandbox_workspace_dir=config.workspace_mount_path_in_sandbox,
        cache_dir=config.cache_dir,
        run_as_devin=config.run_as_devin,
        sid=sid,
    )

    requirements_host_src = 'evaluation/mint/requirements.txt'
    requirements_sandbox_dest = '/opendevin/plugins/mint/requirements.txt'
    sandbox.copy_to(
        host_src=requirements_host_src,
        sandbox_dest=requirements_sandbox_dest,
        recursive=False,
    )
    logger.info(
        f'Copied files from [{requirements_host_src}] to [{requirements_sandbox_dest}] inside sandbox.'
    )
    exit_code, output = sandbox.execute(f'pip install -r {requirements_sandbox_dest}')

    # Prepare instruction
    assert metadata.details is not None
    instruction = ToolPromptTemplate(use_tool=True)(
        max_total_steps=metadata.max_iterations,
        max_propose_solution=metadata.details['max_propose_solution'],
        in_context_example=instance.in_context_example(
            use_tool=True, with_feedback=False
        ),
        task_prompt='Task:\n' + instance.prompt,
    )
    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you or provide the concise RESULT inside <solution> tag AND NEVER ASK FOR HUMAN HELP.\n'

    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    fake_user_response_fn = functools.partial(
        AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[agent.__class__.__name__],
        task=instance,
        task_config={
            'max_iterations': metadata.max_iterations,
            'max_propose_solution': metadata.details['max_propose_solution'],
        },
    )

    state: State | None = asyncio.run(
        run_agent_controller(
            agent,
            instruction,
            max_iterations=metadata.max_iterations,
            max_budget_per_task=config.max_budget_per_task,
            fake_user_response_fn=fake_user_response_fn,
            sandbox=sandbox,
            sid=sid,
        )
    )

    if state is None:
        raise ValueError('State should not be None.')

    task_state = None
    if hasattr(state, 'task_state'):
        task_state = state.task_state
        logger.info('Task state: ' + str(task_state.to_dict()))

    metrics = state.metrics.get() if state.metrics else None

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = state.history.compatibility_for_eval_history_pairs()

    # Save the output
    output = {
        'id': instance.task_id,
        'instance': instance.to_dict(),
        'instruction': instruction,
        'metadata': metadata.model_dump(),
        'history': histories,
        'metrics': metrics,
        'error': state.last_error if state and state.last_error else None,
        'test_result': task_state.success if task_state else False,
    }

    # Close the sandbox
    sandbox.close()

    return output


if __name__ == '__main__':
    parser = get_parser()

    parser.add_argument(
        '--subset',
        default='math',
        choices=['math', 'gsm8k', 'mmlu', 'theoremqa', 'mbpp', 'humaneval'],
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
    # so we don't need to manage file uploading to OpenDevin's repo
    mint_dataset = load_dataset(
        'ryanhoangt/xingyaoww-mint-bench', name=args.subset, split='test'
    )
    logger.info(f'Evaluating MINT - {args.subset} subset')
    mint_tests = mint_dataset.to_pandas()

    id_column = 'id'
    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    logger.info(f'Config for evaluation: {config}')

    metadata = make_metadata(
        llm_config,
        args.dataset_name,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
        details={'max_propose_solution': args.max_propose_solution},
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(mint_dataset, output_file, args.eval_n_limit, id_column)
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
