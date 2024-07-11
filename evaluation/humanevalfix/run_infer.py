"""
Implements evaluation of agents on HumanEvalFix from the HumanEvalPack benchmark introduced in
"OctoPack: Instruction Tuning Code Large Language Models" (https://arxiv.org/abs/2308.07124).
Please see https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/humanevalpack.py
for the reference implementation used in the paper.

TODOs:
- Potentially support other HumanEvalPack datasets (Explain & Synthesize)
- Support other languages (currently only Python)
"""

import asyncio
import logging
import os
import pathlib

import pandas as pd
from datasets import load_dataset
from evaluate import load

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
from opendevin.core.config import config, get_llm_config_arg, parse_arguments
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM

IMPORT_HELPER = {
    'python': [
        'import math',
        'import re',
        'import sys',
        'import copy',
        'import datetime',
        'import itertools',
        'import collections',
        'import heapq',
        'import statistics',
        'import functools',
        'import hashlib',
        'import numpy',
        'import numpy as np',
        'import string',
        'from typing import *',
        'from collections import *',
    ],
}

LANGUAGE_TO_TIMEOUT = {
    'python': 10,
}

LANGUAGE_TO_NUM_WORKERS = {
    'python': 4,
}

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'MonologueAgent': monologue_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n'
}


def get_test_result(instance, path, language='python', timeout=10):
    # Evaluation reference: https://github.com/bigcode-project/bigcode-evaluation-harness/blob/84b96da31b7f840b55c5733325346176140cdb6b/bigcode_eval/tasks/humanevalpack.py#L347
    test_result = {'result': {}, 'metadata': {}}
    code_metric = load('Muennighoff/code_eval_octopack')
    timeout = LANGUAGE_TO_TIMEOUT[language]
    num_workers = LANGUAGE_TO_NUM_WORKERS[language]
    python_imports = '\n'.join(IMPORT_HELPER[language])

    # Load function from path
    with open(path, 'r') as f:
        function = f.read()

    function = [[python_imports + '\n' + function.strip()]]

    results, logs = code_metric.compute(
        references=[instance.test],
        predictions=function,
        language=language,
        timeout=timeout,
        num_workers=num_workers,
    )
    test_result['result'] = results
    test_result['metadata'] = {
        'logs': logs,
        'timeout': timeout,
        'num_workers': num_workers,
    }
    return test_result


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(llm_config=metadata.llm_config))
    old_workspace_mount_path = config.workspace_mount_path
    old_workspace_base = config.workspace_base

    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        # create process-specific workspace dir
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

        # reset workspace to config
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        # use a session id for concurrent evaluation
        sid = instance.task_id.replace('/', '__')

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                metadata.eval_output_dir,
                'logs',
                f'instance_{sid}.log',
            )
            # Remove all existing handlers from logger
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # add back the console handler to print ONE line
            logger.addHandler(get_console_handler())
            logger.info(
                f'Starting evaluation for instance {instance.task_id}.\nLOG:   tail -f {log_file}'
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

        # Create file with HumanEvalFix problem
        # Prompt reference: https://github.com/bigcode-project/bigcode-evaluation-harness/blob/84b96da31b7f840b55c5733325346176140cdb6b/bigcode_eval/tasks/humanevalpack.py#L509
        problem_statement = (
            instance.declaration + instance.buggy_solution + '\n' + instance.test
        )
        path = os.path.join(workspace_mount_path, f'{sid}.py')
        with open(path, 'w') as f:
            f.write(problem_statement)

        # Prepare instruction
        instruction = (
            f'Please fix the function in {instance.task_id.replace("/", "__")}.py such that all test cases pass.\n'
            'Environment has been set up for you to start working. You may assume all necessary tools are installed.\n\n'
            '# Problem Statement\n'
            f'{problem_statement}\n\n'
        )
        instruction += (
            'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
            'You should NOT modify any existing test case files. If needed, you can add new test cases in a NEW file to reproduce the issue.\n'
            'You SHOULD INCLUDE PROPER INDENTATION in your edit commands.\n'
        )
        # NOTE: You can actually set slightly different instruction for different agents
        instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State | None = asyncio.run(
            run_agent_controller(
                agent,
                instruction,
                max_iterations=metadata.max_iterations,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                    agent.__class__.__name__
                ),
                sid=sid,
            )
        )

        # ======= Attempt to evaluate the agent's edits =======
        test_result = get_test_result(instance, path)

        # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
        # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.
        if state is None:
            raise ValueError('State should not be None.')
        metrics = state.metrics.get() if state.metrics else None

        # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
        # for compatibility with the existing output format, we can remake the pairs here
        # remove when it becomes unnecessary
        histories = state.history.compatibility_for_eval_history_pairs()

        # Save the output
        output = {
            'task_id': instance.task_id,
            'instruction': instruction,
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
        config.workspace_base = old_workspace_base
    return output


if __name__ == '__main__':
    args = parse_arguments()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset(
        'bigcode/humanevalpack', 'python'
    )  # TODO: Support other languages
    hefix_tests = dataset['test'].to_pandas()

    id_column = 'task_id'

    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    logger.info(f'Config for evaluation: {config}')

    metadata = make_metadata(
        llm_config,
        args.dataset_name,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
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
