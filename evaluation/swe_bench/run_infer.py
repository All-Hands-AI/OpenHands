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
import toml
import whatthepatch
from datasets import load_dataset
from tqdm import tqdm

import agenthub
from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict

USE_HINT_TEXT = os.environ.get('USE_HINT_TEXT', 'false') == 'true'


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
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
    instance: dict,
    agent_class: str,
    metadata: dict,
    skip_workspace_mount: bool,
    eval_output_dir: str,
    reset_logger: bool = True,
):
    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    # create process-specific workspace dir
    # if `not skip_workspace_mount` - we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    if not skip_workspace_mount:
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            eval_output_dir, 'logs', f'instance_{instance.instance_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance.instance_id}.\nHint: run "tail -f {log_file}" to see live logs in a seperate shell'
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

    if not skip_workspace_mount:
        logger.info(f'Process-specific workspace mounted at {workspace_mount_path}')

    # NOTE: this is something special we do for SWE-Bench due to the reason described in the previous section
    # You can omit this if you don't need to setup specialized sandbox
    workspace_dir_name = f'{instance.repo}__{instance.version}'.replace('/', '__')
    sandbox = SWEBenchSSHBox.get_box_for_instance(
        instance,
        workspace_dir_name,
        skip_workspace_mount=skip_workspace_mount,
        workspace_mount_path=workspace_mount_path,
        sandbox_plugins=agenthub.Agent.get_cls(agent_class).sandbox_plugins,
    )

    # Prepare instruction
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
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
            sandbox=sandbox,
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

    # Save the output
    output = {
        'instance_id': instance.instance_id,
        'swe_instance': instance.to_dict(),  # SWE Bench specific
        'instruction': instruction,
        'git_patch': git_patch,  # SWE Bench specific
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'metrics': metrics,
        'error': state.error if state and state.error else None,
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
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_tests = filter_dataset(dataset['test'].to_pandas(), 'instance_id')

    # Check https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/README.md#configure-opendevin-and-your-llm
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
        'swe_bench_lite',
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
        swe_bench_tests = swe_bench_tests.head(eval_n_limit)
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_instance_ids.add(data['instance_id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_instance_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_swe_bench_tests = []
    for idx, instance in swe_bench_tests.iterrows():
        if instance.instance_id in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance.instance_id} as it is already finished.'
            )
            continue
        new_swe_bench_tests.append(instance)

    swe_bench_tests = pd.DataFrame(new_swe_bench_tests)
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(swe_bench_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(swe_bench_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["instance_id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        logger.info(
            f'Finished evaluation for instance {output["instance_id"]}: {output["test_result"]["result"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    # This is SWE-Bench specific - CodeActAgent doesn't require mounted workspace to work
    skip_workspace_mount = agent_class == 'CodeActAgent'
    logger.info(f'Skipping workspace mount: {skip_workspace_mount}')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for row_idx, instance in swe_bench_tests.iterrows():
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
                    skip_workspace_mount,
                    eval_output_dir,
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
