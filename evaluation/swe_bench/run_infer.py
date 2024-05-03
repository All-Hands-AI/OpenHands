import asyncio
import json
import os
import pathlib
import time

import whatthepatch
from datasets import load_dataset
from tqdm import tqdm

from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import args
from opendevin.core.logger import get_file_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.observation import UserMessageObservation


def codeact_user_response(state: State) -> str:
    if state.history:
        user_msg_obs = [
            obs for _, obs in state.history if isinstance(obs, UserMessageObservation)
        ]
        if len(user_msg_obs) >= 3:
            # let the agent know that it can give up when it has tried 3 times
            return 'Please continue working on the task on whatever approach you think is suitable. If you think you have modified the code in a way that fixes the issue OR you want to give up, please run the following command: <execute_bash> exit </execute_bash>.\n'
    return (
        'Please continue working on the task on whatever approach you think is suitable. '
        'If you think you have modified the code in a way that fixes the issue, please run the following command: <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK. '
    )


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {'CodeActAgent': codeact_user_response}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n'
}


def get_test_result(instance, sandbox, workspace_dir_name):
    test_result = {'result': {}, 'metadata': {}}
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
            key, value = line.split(':')
            value = value.strip()
            try:
                value = int(value)
            except ValueError:
                pass
            test_result['result'][key.strip()] = value
    return test_result


if __name__ == '__main__':
    # Load the dataset
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_lite_test = dataset['test'].to_pandas()

    # TEST METADATA
    agent_class = args.agent_cls
    assert (
        agent_class in AGENT_CLS_TO_FAKE_USER_RESPONSE_FN
    ), f'Unsupported agent class: {agent_class}'
    model_name = args.model_name
    max_iterations = args.max_iterations
    eval_output_dir = os.path.join(
        args.eval_output_dir,
        'swe_bench',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations),
    )

    # logger save to eval_output_dir/infer.log
    logger.addHandler(get_file_handler(eval_output_dir))
    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    metadata = {
        'agent_class': agent_class,
        'model_name': model_name,
        'max_iterations': max_iterations,
        'eval_output_dir': eval_output_dir,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(os.path.join(eval_output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        swe_bench_lite_test = swe_bench_lite_test.head(eval_n_limit)
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

    pbar = tqdm(swe_bench_lite_test.iterrows(), total=len(swe_bench_lite_test))

    for row_idx, instance in swe_bench_lite_test.iterrows():
        if instance.instance_id in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance.instance_id} as it is already finished.'
            )
            pbar.update()
            continue

        workspace_dir_name = f'{instance.repo}__{instance.version}'.replace('/', '__')
        pbar.set_description(f'Instance {instance.instance_id} | {workspace_dir_name}')
        sandbox = SWEBenchSSHBox.get_box_for_instance(instance, workspace_dir_name)

        # Prepare controller kwargs
        controller_kwargs = {
            'fake_user_response_fn': AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                agent_class
            ),
            'sandbox': sandbox,
        }

        # Prepare instruction
        instruction = (
            f'Please fix the following issue for the repository in /workspace/{workspace_dir_name}.\n'
            'Environment has been set up for you to start working. You may assume all necessary tools are installed.\n\n'
            '# Problem Statement\n'
            f'{instance.problem_statement}\n\n'
        )
        if instance.hints_text:
            instruction += f'# Hints\n{instance.hints_text}\n\n'
        instruction += (
            'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK \n'
            'You should ONLY interact with the environment provided to you.\n'
            # 'You should NOT modify any existing test case files. '
            # 'If needed, you can add new test cases in a NEW file to reproduce the issue.\n'
        )
        instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

        # Run the agent
        state: State = asyncio.run(
            main(instruction, controller_kwargs=controller_kwargs)
        )

        # Get git patch
        git_patch = sandbox.get_diff_patch()
        logger.info(f'Got git diff for instance {instance.instance_id}')

        # ======= Attempt to evaluate the agent's edits =======
        # Attempt to analyze the test patch to get involved filepaths
        test_result = get_test_result(instance, sandbox, workspace_dir_name)
        pbar.update()
        pbar.set_postfix_str(f'Test Result: {test_result["result"]}')

        # Save the output
        output = {
            'instance_id': instance.instance_id,
            'swe_instance': instance.to_dict(),
            'instruction': instruction,
            'git_patch': git_patch,
            'metadata': metadata,
            'history': [
                (action.to_dict(), obs.to_dict()) for action, obs in state.history
            ],
            'test_result': test_result,
        }
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    output_fp.close()
    logger.info('Evaluation finished.')
