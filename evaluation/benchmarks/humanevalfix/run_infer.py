"""Implements evaluation of agents on HumanEvalFix from the HumanEvalPack benchmark introduced in
"OctoPack: Instruction Tuning Code Large Language Models" (https://arxiv.org/abs/2308.07124).
Please see https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/humanevalpack.py
for the reference implementation used in the paper.

TODOs:
- Potentially support other HumanEvalPack datasets (Explain & Synthesize)
- Support other languages (currently only Python)
"""

import asyncio
import os
import tempfile
from typing import Any

import pandas as pd
from datasets import load_dataset
from evaluate import load

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    codeact_user_response,
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
    parse_arguments,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

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
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please finish the interaction using the "finish" tool.\n'
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=SandboxConfig(
            base_container_image='python:3.12-bookworm',
            enable_auto_lint=True,
            use_host_network=False,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    return config


def _get_instance_id(instance: pd.Series) -> str:
    return instance.instance_id.replace('/', '__')


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Initialization Fn {'-' * 50}")
    obs: CmdOutputObservation

    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command='cd /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    problem_statement = (
        instance.declaration + instance.buggy_solution + '\n' + instance.test
    )
    filename = f'{_get_instance_id(instance)}.py'
    with tempfile.TemporaryDirectory() as tmpdir:
        host_script_path = os.path.join(tmpdir, filename)
        with open(host_script_path, 'w') as f:
            f.write(problem_statement)
        runtime.copy_to(
            host_script_path,
            '/workspace',
        )

    # check file exists
    action = CmdRunAction(command=f'ls /workspace/{_get_instance_id(instance)}.py')
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    logger.info(f"{'-' * 50} END Runtime Initialization Fn {'-' * 50}")


def complete_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required, but it is used to get the workspace_dir_name
) -> dict[str, Any]:
    """Complete the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    If you need to do something in the sandbox to get the correctness metric after
    the agent has run, modify this function.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Completion Fn {'-' * 50}")
    obs: CmdOutputObservation

    # default value
    language = 'python'
    timeout = 10

    test_result = {'result': {}, 'metadata': {}}
    code_metric = load('Muennighoff/code_eval_octopack')
    timeout = LANGUAGE_TO_TIMEOUT[language]
    num_workers = LANGUAGE_TO_NUM_WORKERS[language]
    python_imports = '\n'.join(IMPORT_HELPER[language])

    action = CmdRunAction(
        command=f'cat /workspace/{_get_instance_id(instance)}.py', keep_prompt=False
    )
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    function = obs.content.replace('\r\n', '\n')
    logger.info(f'Function: {function}')
    function = [[python_imports + '\n' + function]]

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
    logger.info(f"{'-' * 50} END Runtime Completion Fn {'-' * 50}")
    return test_result


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(metadata)
    # use a session id for concurrent evaluation
    sid = _get_instance_id(instance)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    # Create file with HumanEvalFix problem
    # Prompt reference: https://github.com/bigcode-project/bigcode-evaluation-harness/blob/84b96da31b7f840b55c5733325346176140cdb6b/bigcode_eval/tasks/humanevalpack.py#L509
    problem_statement = (
        instance.declaration + instance.buggy_solution + '\n' + instance.test
    )

    # Prepare instruction
    instruction = (
        f'Please fix the function in {sid}.py such that all test cases pass.\n'
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
    instruction += AGENT_CLS_TO_INST_SUFFIX[metadata.agent_class]

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    initialize_runtime(runtime, instance)
    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=MessageAction(content=instruction),
            runtime=runtime,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                metadata.agent_class
            ),
        )
    )

    if state is None:
        raise ValueError('State should not be None.')
    metrics = state.metrics.get() if state.metrics else None
    test_result = complete_runtime(runtime, instance)

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=instance.instance_id,
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result=test_result,
    )
    return output


if __name__ == '__main__':
    args = parse_arguments()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenHands's repo
    dataset = load_dataset(
        'bigcode/humanevalpack', 'python'
    )  # TODO: Support other languages
    hefix_tests = dataset['test'].to_pandas()
    hefix_tests.rename(columns={'task_id': 'instance_id'}, inplace=True)

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'humanevalfix-python',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(hefix_tests, output_file, args.eval_n_limit)

    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
    )
