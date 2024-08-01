import asyncio
import logging
import os
import re

import nltk
import pandas as pd
from datasets import load_dataset

from evaluation.utils.shared import (
    EvalMetadata,
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import get_llm_config_arg, load_app_config, parse_arguments
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_controller
from opendevin.llm.llm import LLM

config = load_app_config()

# Only CodeActAgent can delegate to BrowsingAgent
SUPPORTED_AGENT_CLS = {'CodeActAgent'}


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(config=metadata.llm_config))
    env_id = instance.instance_id
    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            metadata.eval_output_dir, 'logs', f'instance_{env_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {env_id}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
    else:
        logger.info(f'Starting evaluation for instance {env_id}.')

    instruction = (
        f'You can delegate browsing tasks to a browser agent. '
        f"For example, for query 'Who is the president of the United States?', you can delegate the task to a browser agent via <execute_browse> Who is the president of the United States? </execute_browse>.\n"
        f'Now, solve the following query: "{instance.instruction}"\n'
        f'NOTE: You should copy the "query" as is into the <execute_browse> tag. DO NOT change ANYTHING in the query.'
    )

    config.max_iterations = metadata.max_iterations
    state: State | None = asyncio.run(
        run_controller(
            config=config,
            task_str=instruction,
            agent=agent,
            sid=env_id,
        )
    )

    # ======= Attempt to evaluate the agent's environment impact =======

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    metrics = state.metrics.get() if state.metrics else None
    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = state.history.compatibility_for_eval_history_pairs()

    # find the last delegate action
    last_delegate_action = None
    result = {}
    for action, _ in histories:
        if action['action'] == 'delegate':
            last_delegate_action = action
            instruction_for_delegate = action['args']['inputs']['task']
            # parse `browse_actions` from `instruction_for_delegate`
            # task = f'{thought}. I should start with: {browse_actions}'
            instruction_for_delegate = re.search(
                r'I should start with: (.*)', instruction_for_delegate
            ).group(1)

            # calculate the edit distance between the instance.instruction and the instruction_for_delegate
            edit_distance = nltk.edit_distance(
                instance.instruction, instruction_for_delegate
            )
            is_exact_match = (
                instance.instruction.strip() == instruction_for_delegate.strip()
            )
            result['edit_distance'] = edit_distance
            result['is_exact_match'] = is_exact_match

    # Save the output
    output = {
        'instance_id': env_id,
        'instruction': instruction,
        'metadata': metadata.model_dump(),
        'history': histories,
        'metrics': metrics,
        'error': state.last_error if state and state.last_error else None,
        'test_result': {
            'query': instance.instruction,
            'action': last_delegate_action,
            'result': result,
        },
    }

    return output


if __name__ == '__main__':
    args = parse_arguments()

    dataset = load_dataset('OpenDevin/eval-browsing-instructions')
    dataset = dataset['train'].to_pandas()
    assert dataset.columns.tolist() == ['instance_id', 'instruction']
    id_column = 'instance_id'
    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    logger.info(f'Config for evaluation: {config}')

    metadata = make_metadata(
        llm_config,
        'browsing_delegation',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    if metadata.agent_class not in SUPPORTED_AGENT_CLS:
        raise ValueError(
            f'Agent class {metadata.agent_class} not supported with AgentDelegation.'
        )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(dataset, output_file, args.eval_n_limit, id_column)
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
