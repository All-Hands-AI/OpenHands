import asyncio
import logging
import os
import pathlib

import pandas as pd
import toml
import whatthepatch
from datasets import load_dataset

import agenthub
from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox
from evaluation.utils.shared import (
    EvalMetadata,
    codeact_user_response,
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import get_llm_config_arg, load_app_config, parse_arguments
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM

config = load_app_config()

USE_HINT_TEXT = os.environ.get('USE_HINT_TEXT', 'false') == 'true'
USE_INSTANCE_IMAGE = os.environ.get('USE_INSTANCE_IMAGE', 'false') == 'true'

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'CodeActSWEAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n',
    'CodeActSWEAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n',
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

    if USE_INSTANCE_IMAGE:
        # instance report is not supported in instance image mode
        test_result['metadata']['6_get_instance_report_success'] = False
        test_result['metadata']['6_get_instance_report_error'] = (
            'Instance report is not supported in instance image mode.'
        )

    else:
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
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(config=metadata.llm_config))

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
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
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
        workspace_mount_path=workspace_mount_path,
        sandbox_plugins=agenthub.Agent.get_cls(metadata.agent_class).sandbox_plugins,
        use_instance_image=USE_INSTANCE_IMAGE,
    )

    # Prepare instruction
    if metadata.agent_class == 'CodeActSWEAgent':
        instruction = (
            'We are currently solving the following issue within our repository. Here is the issue text:\n'
            '--- BEGIN ISSUE ---\n'
            f'{instance.problem_statement}\n'
            '--- END ISSUE ---\n\n'
        )

        if USE_HINT_TEXT and instance.hints_text:
            instruction += (
                f'--- BEGIN HINTS ---\n{instance.hints_text}\n--- END HINTS ---\n'
            )
        instruction += f"""Now, you're going to solve this issue on your own. Your terminal session has started and you're in the repository's root directory. You can use any bash commands or the special interface to help you. Edit all the files you need to and run any checks or tests that you want.
Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME. You should always wait for feedback after every command.
When you're satisfied with all of the changes you've made, you can run the following command: <execute_bash> exit </execute_bash>.
Note however that you cannot use any interactive session commands (e.g. vim) in this environment, but you can write scripts and run them. E.g. you can write a python script and then run it with `python <script_name>.py`.

NOTE ABOUT THE EDIT COMMAND: Indentation really matters! When editing a file, make sure to insert appropriate indentation before each line!

IMPORTANT TIPS:
1. Always start by trying to replicate the bug that the issues discusses.
    If the issue includes code for reproducing the bug, we recommend that you re-implement that in your environment, and run it to make sure you can reproduce the bug.
    Then start trying to fix it.
    When you think you've fixed the bug, re-run the bug reproduction script to make sure that the bug has indeed been fixed.

    If the bug reproduction script does not print anything when it successfully runs, we recommend adding a print("Script completed successfully, no errors.") command at the end of the file,
    so that you can be sure that the script indeed ran fine all the way through.

2. If you run a command and it doesn't work, try running a different command. A command that did not work once will not work the second time unless you modify it!

3. If you open a file and need to get to an area around a specific line that is not in the first 100 lines, say line 583, don't just use the scroll_down command multiple times. Instead, use the goto 583 command. It's much quicker.

4. If the bug reproduction script requires inputting/reading a specific file, such as buggy-input.png, and you'd like to understand how to input that file, conduct a search in the existing repo code, to see whether someone else has already done that. Do this by running the command: find_file("buggy-input.png") If that doesn't work, use the linux 'find' command.

5. Always make sure to look at the currently open file and the current working directory (which appears right after the currently open file). The currently open file might be in a different directory than the working directory! Note that some commands, such as 'create', open files, so they might change the current  open file.

6. When editing files, it is easy to accidentally specify a wrong line number or to write code with incorrect indentation. Always check the code after you issue an edit to make sure that it reflects what you wanted to accomplish. If it didn't, issue another command to fix it.

[Current directory: /workspace/{workspace_dir_name}]
"""
    else:
        # Testing general agents
        instruction = (
            f'Please fix the following issue for the repository in /workspace/{workspace_dir_name}.\n'
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
        )

    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]

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
