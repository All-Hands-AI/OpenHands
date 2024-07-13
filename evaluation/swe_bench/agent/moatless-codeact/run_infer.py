import asyncio
import logging
import multiprocessing as mp
import os
import pathlib

import pandas as pd
import toml
import whatthepatch
from datasets import load_dataset

import agenthub
from agenthub.moatless_search_agent import MoatlessCodeActAgent
from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox
from evaluation.utils.shared import (
    EvalMetadata,
    codeact_user_response,
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, parse_arguments
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM

USE_HINT_TEXT = os.environ.get('USE_HINT_TEXT', 'false') == 'true'


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'MoatlessCodeActAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'MoatlessCodeActAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n',
}


def get_test_result(instance, sandbox, workspace_dir_name):
    test_result = {'result': {}, 'metadata': {}}
    # NOTE: if you need to do something in the sandbox to get the correctness metric, modify this function
    try:
        test_patch_parsed = whatthepatch.parse_patch(instance.test_patch)
        # get a list of filepaths that are involved in the patch
        involved_filepaths = set()
        for patch in test_patch_parsed:
            involved_filepaths.add(patch.header.old_path.removeprefix('a/'))
            involved_filepaths.add(patch.header.new_path.removeprefix('b/'))
        involved_filepaths = list(involved_filepaths)
        test_result['metadata']['1_test_patch_parse_success'] = True
        test_result['metadata']['1_test_involved_filepaths'] = involved_filepaths
    except Exception as e:
        logger.error(
            f'Error parsing test patch for instance {instance.instance_id}: {e}'
        )
        test_result['metadata']['1_test_patch_parse_success'] = False
        test_result['metadata']['1_test_patch_parse_error'] = str(e)
        test_result['metadata']['1_test_involved_filepaths'] = None
        involved_filepaths = []

    # Try to revert the changes for involved filepaths
    err_code, output = sandbox.execute(f'cd /workspace/{workspace_dir_name}')
    test_result['metadata']['2_revert_test_involved_filepaths_success'] = []
    for filepath in involved_filepaths:
        err_code, output = sandbox.execute(
            f'git checkout {instance["base_commit"]} -- {filepath}'
        )
        if err_code != 0:
            logger.error(f'Error reverting changes for {filepath}: {output}')
            test_result['metadata']['2_revert_test_involved_filepaths_success'].append(
                False
            )
        else:
            test_result['metadata']['2_revert_test_involved_filepaths_success'].append(
                True
            )

    # Apply the testcase
    err_code, output = sandbox.execute('git apply $SWE_TASK_DIR/test.patch')
    if err_code != 0:
        logger.error(f'Error applying test patch: {output}')
        test_result['metadata']['3_apply_test_patch_success'] = False
        test_result['metadata']['3_apply_test_patch_error'] = output
    else:
        test_result['metadata']['3_apply_test_patch_success'] = True

    # Run the test command
    err_code, output = sandbox.execute(
        '$TEST_CMD > /workspace/$SWE_INSTANCE_ID.log 2>&1'
    )
    if err_code != 0:
        logger.error(f'Error running test command: {output}')
        test_result['metadata']['4_run_test_command_success'] = False
        test_result['metadata']['4_run_test_command_error'] = output
    else:
        test_result['metadata']['4_run_test_command_success'] = True

    # Get the test output
    err_code, output = sandbox.execute('cat /workspace/$SWE_INSTANCE_ID.log')
    if err_code != 0:
        logger.error(f'Error getting test output: {output}')
        test_result['metadata']['4_get_test_output_success'] = False
        test_result['metadata']['4_get_test_output_error'] = output
    else:
        test_result['metadata']['4_get_test_output_success'] = True
        test_result['test_output'] = output

    # Reformat instance.json
    # $SWE_TASK_DIR/instance.json is a dict {"XXX": "YYY"}, add a [ before and a ] after
    err_code, output = sandbox.execute(
        (
            'cat $SWE_TASK_DIR/instance.json | sed "s/^{/[{/" | sed "s/}$/}]/" > /workspace/instance.json'
        )
    )
    if err_code != 0:
        logger.error(f'Error creating instance.json: {output}')
        test_result['metadata']['5_reformat_instance_json_success'] = False
        test_result['metadata']['5_reformat_instance_json_error'] = output
    else:
        test_result['metadata']['5_reformat_instance_json_success'] = True

    # Get the instance report
    err_code, output = sandbox.execute(
        (
            'cd /swe_util/OD-SWE-bench '
            '&& export PYTHONPATH=$(pwd):$PYTHONPATH '
            '&& conda run -n swe-bench-eval python swebench/metrics/get_instance_report.py --swe_bench_task /workspace/instance.json --log_path /workspace/$SWE_INSTANCE_ID.log'
        )
    )
    if err_code != 0:
        logger.error(f'Error getting instance report: {output}')
        test_result['metadata']['6_get_instance_report_success'] = False
        test_result['metadata']['6_get_instance_report_error'] = output
    else:
        test_result['metadata']['6_get_instance_report_success'] = True
        test_result['result_raw'] = output

        # try to parse output
        for line in output.strip().split('\n'):
            line = line.strip('-')
            try:
                key, value = line.split(':')
            except ValueError:
                # skip this line
                print(f'Error parsing result line: {line}')
                continue
            value = value.strip()
            try:
                value = int(value)
            except ValueError:
                pass
            test_result['result'][key.strip()] = value
    return test_result


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = MoatlessCodeActAgent(llm=LLM(llm_config=metadata.llm_config))

    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    # create process-specific workspace dir
    workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            metadata.eval_output_dir,
            'infer_logs',
            f'instance_{instance.instance_id}.log',
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance.instance_id}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
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
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    # NOTE: this is something special we do for SWE-Bench due to the reason described in the previous section
    # You can omit this if you don't need to setup specialized sandbox
    workspace_dir_name = f'{instance.repo}__{instance.version}'.replace('/', '__')
    sandbox = SWEBenchSSHBox.get_box_for_instance(
        instance,
        workspace_dir_name,
        skip_workspace_mount=False,
        workspace_mount_path=workspace_mount_path,
        sandbox_plugins=agenthub.Agent.get_cls('CodeActAgent').sandbox_plugins,
    )

    # Prepare instruction
    # Testing general agents
    instruction = (
        f'Please fix the following issue for the repository in /workspace/{workspace_dir_name} in 2 stages:\n'
        '- The first stage MUST be to execute search ONCE with the WHOLE issue description to find the relevant code snippet, using <execute_search> ... </execute_search>. Execute this ONCE is enough and that will help you find all the code snippets that cause the issue.\n'
        '- In the second stage, you must edit ONLY those code snippets found in the previous stage to fix the issue.\n\n'
        'Environment has been set up for you to start working. You may assume all necessary tools are installed.\n\n'
        '# Problem Statement\n'
        f'{instance.problem_statement}\n\n'
    )
    if USE_HINT_TEXT and instance.hints_text:
        instruction += f'# Hints\n{instance.hints_text}\n\n'
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        'You should NOT modify any existing test case files. If needed, you can add new test cases in a NEW file to reproduce the issue.\n'
        'You SHOULD INCLUDE PROPER INDENTATION in your edit commands.\n'
        "Let's start by executing <execute_search> <full user problem statement above> </execute_search> to find the relevant code snippets.\n"
    )

    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State | None = asyncio.run(
        run_agent_controller(
            agent,
            instruction,
            max_iterations=metadata.max_iterations,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                agent.__class__.__name__
            ],
            sandbox=sandbox,
            sid=instance.instance_id,
        )
    )

    # ======= THIS IS SWE-Bench specific =======
    # Get git patch
    git_patch = sandbox.get_diff_patch()
    logger.info(f'Got git diff for instance {instance.instance_id}')
    # ==========================================

    # ======= Attempt to evaluate the agent's edits =======
    # TODO: if you need to do something in the sandbox to get the correctness metric, modify this function
    test_result = get_test_result(instance, sandbox, workspace_dir_name)

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
        'instance_id': instance.instance_id,
        'swe_instance': instance.to_dict(),  # SWE Bench specific
        'instruction': instruction,
        'git_patch': git_patch,  # SWE Bench specific
        'metadata': metadata.model_dump(),
        'history': histories,
        'metrics': metrics,
        'error': state.last_error if state and state.last_error else None,
        'test_result': test_result,
    }

    # Close the sandbox
    sandbox.close()
    return output


def filter_dataset(dataset: pd.DataFrame, filter_column: str) -> pd.DataFrame:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.toml')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = toml.load(file)
            if 'selected_ids' in data:
                selected_ids = data['selected_ids']
                logger.info(
                    f'Filtering {len(selected_ids)} tasks from "selected_ids"...'
                )
                subset = dataset[dataset[filter_column].isin(selected_ids)]
                logger.info(f'Retained {subset.shape[0]} tasks after filtering')
                return subset
    return dataset


if __name__ == '__main__':
    args = parse_arguments()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_tests = filter_dataset(dataset['test'].to_pandas(), 'instance_id')

    id_column = 'instance_id'
    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    if args.llm_config and llm_config is None:
        raise ValueError(f'Could not find LLM config {args.llm_config}')
    logger.info(f'Config for evaluation: {config}')

    details = {}
    _agent_cls = agenthub.Agent.get_cls(args.agent_cls)
    if hasattr(_agent_cls, 'system_message'):
        details['system_message'] = _agent_cls.system_message
    if hasattr(_agent_cls, 'in_context_example'):
        details['in_context_example'] = _agent_cls.in_context_example

    metadata = make_metadata(
        llm_config,
        'swe-bench-lite',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
        details=details,
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(
        swe_bench_tests, output_file, args.eval_n_limit, id_column
    )
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
