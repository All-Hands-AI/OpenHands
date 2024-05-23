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
import json
import logging
import multiprocessing as mp
import os
import pathlib
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
from datasets import load_dataset
from evaluate import load
from tqdm import tqdm

from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict

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


def cleanup():
    logger.info('Cleaning up child processes...')
    for process in mp.active_children():
        logger.info(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have modified the code in a way that fixes the issue, please run the following command: <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK.\n'
    )
    if state.history:
        user_msgs = [
            action
            for action, _ in state.history
            if isinstance(action, MessageAction) and action.source == 'user'
        ]
        if len(user_msgs) >= 2:
            # let the agent know that it can give up when it has tried 3 times
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg


def monologue_user_response(state: State) -> str:
    raise NotImplementedError('MonologueAgent should never ask for user responses.')


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
    instance, agent_class, metadata, skip_workspace_mount, reset_logger: bool = True
):
    old_workspace_mount_path = config.workspace_mount_path
    old_workspace_base = config.workspace_base
    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    # create process-specific workspace dir
    # if `not skip_workspace_mount` - we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    if not skip_workspace_mount:
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # reset workspace to config
    config.workspace_base = workspace_mount_path
    config.workspace_mount_path = workspace_mount_path

    # Setup the logger properly, so you can run multi-processing to parallize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            eval_output_dir,
            'logs',
            f'instance_{instance.task_id.replace("/", "__")}.log',
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

    if not skip_workspace_mount:
        logger.info(f'Process-specific workspace mounted at {workspace_mount_path}')

    # Create file with HumanEvalFix problem
    # Prompt reference: https://github.com/bigcode-project/bigcode-evaluation-harness/blob/84b96da31b7f840b55c5733325346176140cdb6b/bigcode_eval/tasks/humanevalpack.py#L509
    problem_statement = (
        instance.declaration + instance.buggy_solution + '\n' + instance.test
    )
    path = os.path.join(
        workspace_mount_path, f'{instance.task_id.replace("/", "__")}.py'
    )
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
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
        )
    )

    # ======= Attempt to evaluate the agent's edits =======
    test_result = get_test_result(instance, path)

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.
    if state is None:
        raise ValueError('State should not be None.')

    # Save the output
    output = {
        'task_id': instance.task_id,
        'instruction': instruction,
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'error': state.error if state and state.error else None,
        'test_result': test_result,
    }

    config.workspace_mount_path = old_workspace_mount_path
    config.workspace_base = old_workspace_base
    return output


if __name__ == '__main__':
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset(
        'bigcode/humanevalpack', 'python'
    )  # TODO: Support other languages
    hefix_tests = dataset['test'].to_pandas()

    # Check https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/humanevalfix/README.md#configure-opendevin-and-your-llm
    # for details of how to set `llm_config`
    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    logger.info(f'Config for evaluation: {config}')

    # TEST METADATA
    agent_class = args.agent_cls
    assert (
        agent_class in AGENT_CLS_TO_FAKE_USER_RESPONSE_FN
    ), f'Unsupported agent class: {agent_class}'
    model_name = config.llm.model.split('/')[-1]
    max_iterations = args.max_iterations
    eval_note = ''
    if args.eval_note is not None:
        eval_note += '_N_' + args.eval_note
    eval_output_dir = os.path.join(
        args.eval_output_dir,
        'humanevalfix',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )

    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_dir, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    metadata = {
        'agent_class': agent_class,
        'model_name': model_name,
        'max_iterations': max_iterations,
        'eval_output_dir': eval_output_dir,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        # get the commit id of current repo for reproduciblity
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        .decode('utf-8')
        .strip(),
    }
    logger.info(f'Metadata: {metadata}')
    with open(os.path.join(eval_output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        hefix_tests = hefix_tests.head(eval_n_limit)
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_instance_ids.add(data['task_id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_instance_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_hefix_tests = []
    for idx, instance in hefix_tests.iterrows():
        if instance.task_id in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance.task_id} as it is already finished.'
            )
            continue
        new_hefix_tests.append(instance)

    hefix_tests = pd.DataFrame(new_hefix_tests)
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(hefix_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(hefix_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["task_id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        logger.info(
            f'Finished evaluation for instance {output["task_id"]}: {output["test_result"]["result"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for row_idx, instance in hefix_tests.iterrows():
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
                    skip_workspace_mount=False,
                    reset_logger=bool(num_workers > 1),
                )
                future.add_done_callback(update_progress)
                futures.append(future)

            # Wait for all futures to complete
            for future in futures:
                future.result()
    except KeyboardInterrupt:
        print('KeyboardInterrupt received. Cleaning up...')
        cleanup()

    output_fp.close()
    logger.info('Evaluation finished.')
