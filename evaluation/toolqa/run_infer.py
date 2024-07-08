import asyncio
import logging
import os
import pathlib
from typing import Any

import pandas as pd

from evaluation.utils.shared import (
    EvalMetadata,
    codeact_user_response,
    make_metadata,
    monologue_user_response,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM

from .utils import download_data, download_tools, encode_question, eval_answer, get_data

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'MonologueAgent': monologue_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have completed the request, please run the following command: <execute_bash> exit </execute_bash>.\n'
}


def process_instance(instance: Any, metadata: EvalMetadata, reset_logger: bool = True):
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(llm_config=metadata.llm_config))
    # create process-specific workspace dir
    # we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    workspace_mount_path = config.workspace_mount_path
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    eval_output_dir = metadata.eval_output_dir
    qid = instance.qid
    question = instance.question
    answer = instance.answer
    if reset_logger:
        # Set up logger
        log_file = os.path.join(eval_output_dir, 'logs', f'instance_{qid}.log')
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {qid}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
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

    # Prepare instruction
    instruction = encode_question(question)
    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]
    # logger.info(f'Instruction:\n{instruction}', extra={'msg_type': 'OBSERVATION'})

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State | None = asyncio.run(
        run_agent_controller(
            agent,
            instruction,
            max_iterations=metadata.max_iterations,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                agent.__class__.__name__
            ],
            sid=qid,
        )
    )
    # ======= Attempt to evaluate the agent's edits =======
    # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    # retrieve the last message from the agent
    model_answer_raw = state.history.get_last_agent_message()

    # attempt to parse model_answer
    correct = eval_answer(str(model_answer_raw), str(answer))
    logger.info(f'Final message: {model_answer_raw} | Correctness: {correct}')

    metrics = state.metrics.get() if state.metrics else None

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = state.history.compatibility_for_eval_history_pairs()

    # Save the output
    output = {
        'qid': qid,
        'text': model_answer_raw,
        'correct': correct,
        'answer_id': 'None',
        'model_id': metadata.model_name,
        'metadata': metadata.model_dump(),
        'history': histories,
        'metrics': metrics,
        'error': state.last_error if state and state.last_error else None,
    }
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        help='Which dataset to evaluate from ToolQA. ToolQA contains 8 datasets, namely agenda, airbnb, coffee, dblp, flight, gsm8k, scirex, yelp. For example, the default is --dataset flight.',
        default='flight',
    )
    parser.add_argument(
        '--hardness',
        type=str,
        help='Which level of difficulty to evaluate from ToolQA. ToolQA contains 2 levels of hardness, namely easy and hard. For example, the default is --hardness easy.',
        default='easy',
    )
    parser.add_argument(
        '--wolfram_alpha_appid',
        type=str,
        help='wolfram alpha appid to use for wolfram alpha related tests',
        default='YOUR_WOLFRAMALPHA_APPID',
    )
    args, _ = parser.parse_known_args()
    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    logger.info(f'Config for evaluation: {config}')

    dataset = ''
    hardness = ''
    dataset_choices = [
        'agenda',
        'airbnb',
        'coffee',
        'dblp',
        'flight',
        'gsm8k',
        'scirex',
        'yelp',
        'genda',
    ]
    if args.dataset not in dataset_choices:
        raise ValueError(
            'Please choose from agenda, airbnb, coffee, dblp, flight, gsm8k, scirex, yelp for dataset.'
        )
    if args.hardness not in ['easy', 'hard']:
        raise ValueError('Please choose from easy and hard for hardness.')

    # workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    workspace_mount_path = config.workspace_mount_path
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)
    toolqa_test = pd.DataFrame(get_data(dataset, hardness))
    toolqa_data_path = download_data(workspace_mount_path)
    toolqa_tool_path = download_tools(workspace_mount_path, args.wolfram_alpha_appid)

    id_column = 'qid'
    metadata = make_metadata(
        llm_config,
        f'toolqa-{args.dataset}-{args.hardness}',
        args.agent_cls,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(toolqa_test, output_file, args.eval_n_limit, id_column)
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
