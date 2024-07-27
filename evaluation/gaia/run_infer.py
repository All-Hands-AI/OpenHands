import asyncio
import logging
import os
import pathlib
import re
import shutil
from functools import partial

import huggingface_hub
import pandas as pd
from datasets import load_dataset

from evaluation.gaia.scorer import question_scorer
from evaluation.utils.shared import (
    EvalMetadata,
    codeact_user_response,
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
from opendevin.events.action import CmdRunAction, MessageAction
from opendevin.llm.llm import LLM

config = load_app_config()

DATASET_CACHE_DIR = '~/.cache/open-devin/evals/gaia'
DATASET_CACHE_DIR = os.path.expanduser(DATASET_CACHE_DIR)


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': partial(codeact_user_response, encapsulate_solution=True),
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have solved the question, please first send your answer to user through message and then exit.\n'
}


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(config=metadata.llm_config))
    # create process-specific workspace dir
    # we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    old_workspace_mount_path = config.workspace_mount_path

    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)
        config.workspace_mount_path = workspace_mount_path

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        eval_output_dir = metadata.eval_output_dir
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                eval_output_dir, 'logs', f'instance_{instance["task_id"]}.log'
            )
            # Remove all existing handlers from logger
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # add back the console handler to print ONE line
            logger.addHandler(get_console_handler())
            logger.info(
                f'Starting evaluation for instance {instance["task_id"]}.\nLOG:   tail -f {log_file}'
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
        if instance['file_name'] != '':
            # if this question comes with a file, we need to save it to the workspace
            assert metadata.data_split is not None
            src_file = os.path.join(
                DATASET_CACHE_DIR, '2023', metadata.data_split, instance['file_name']
            )
            extension_name = instance['file_name'].split('.')[-1]
            dest_file = os.path.join(workspace_mount_path, f'file.{extension_name}')
            shutil.copyfile(src_file, dest_file)
            logger.info(f'File copied to {dest_file}')
        else:
            dest_file = None

        # Prepare instruction
        instruction = f"{instance['Question']}\n"
        logger.info(f'Instruction: {instruction}')
        if dest_file:
            instruction += f"\n\nThe mentioned file is provided in the workspace at: {dest_file.split('/')[-1]}"

        instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        instruction += 'Please encapsulate your final answer (answer ONLY) within <solution> and </solution>.\n'
        instruction += (
            'For example: The answer to the question is <solution> 42 </solution>.\n'
        )
        # NOTE: You can actually set slightly different instruction for different agents
        instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent.__class__.__name__, '')
        logger.info(f'Instruction:\n{instruction}', extra={'msg_type': 'OBSERVATION'})

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State | None = asyncio.run(
            run_agent_controller(
                agent,
                instruction,
                max_iterations=metadata.max_iterations,
                max_budget_per_task=config.max_budget_per_task,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                    agent.__class__.__name__
                ],
                sid=instance['task_id'],
            )
        )
        # ======= Attempt to evaluate the agent's edits =======
        # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
        # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

        if state is None:
            raise ValueError('State should not be None.')

        model_answer_raw = ''

        # get the last message or thought from the agent
        for event in state.history.get_events(reverse=True):
            if isinstance(event, CmdRunAction) and event.source == 'agent':
                model_answer_raw = event.thought
            elif isinstance(event, MessageAction) and event.source == 'agent':
                model_answer_raw = event.content

        # attempt to parse model_answer
        model_answer = re.findall(r'<solution>(.*?)</solution>', model_answer_raw)
        if len(model_answer) == 0:
            logger.warning(f'Failed to parse model answer: {model_answer_raw}')
            model_answer = model_answer_raw
        else:
            model_answer = model_answer[0]

        logger.info(
            f'Final message: {model_answer} | Ground truth: {instance["Final answer"]}'
        )
        score = question_scorer(
            model_answer=model_answer, ground_truth=instance['Final answer']
        )
        test_result = {
            'score': score,
            'model_answer_raw': model_answer_raw,
            'model_answer': model_answer,
            'ground_truth': instance['Final answer'],
        }
        metrics = state.metrics.get() if state.metrics else None

        # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
        # for compatibility with the existing output format, we can remake the pairs here
        # remove when it becomes unnecessary
        histories = state.history.compatibility_for_eval_history_pairs()

        # Save the output
        output = {
            'instance_id': instance['task_id'],
            'instance': instance,
            'instruction': instance['Question'],
            'metadata': metadata.model_dump(),
            'history': histories,
            'metrics': metrics,
            'error': state.last_error if state and state.last_error else None,
            'test_result': test_result,
        }
    except Exception:
        logger.error('Process instance failed')
        raise
    finally:
        config.workspace_mount_path = old_workspace_mount_path
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--level',
        type=str,
        help='gaia level to evaluate, eg. 2023_level1',
    )
    args, _ = parser.parse_known_args()
    if args.directory:
        config.workspace_base = os.path.abspath(args.directory)
        logger.info(f'Setting workspace base to {config.workspace_base}')

    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    logger.info(f'Config for evaluation: {config}')

    metadata = make_metadata(
        llm_config=llm_config,
        dataset_name='gaia',
        agent_class=args.agent_cls,
        max_iterations=args.max_iterations,
        eval_note=args.eval_note,
        eval_output_dir=args.eval_output_dir,
        data_split=args.data_split,
        details={'gaia-level': args.level},
    )

    dataset = load_dataset('gaia-benchmark/GAIA', args.level)
    huggingface_hub.snapshot_download(
        'gaia-benchmark/GAIA',
        repo_type='dataset',
        local_dir=DATASET_CACHE_DIR,
    )
    gaia_tests = dataset[metadata.data_split]

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    prepared_dataset = prepare_dataset(
        gaia_tests.to_pandas(), output_file, args.eval_n_limit, 'task_id'
    )

    agent = Agent.get_cls(args.agent_cls)(llm=LLM(config.llm))

    run_evaluation(
        dataset=prepared_dataset,
        metadata=metadata,
        output_file=output_file,
        num_workers=args.eval_num_workers,
        process_instance_func=process_instance,
        id_column='task_id',
    )
