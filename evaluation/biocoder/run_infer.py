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
from tqdm import tqdm

import agenthub
from evaluation.biocoder.biocoder_env_box import BiocoderData, BiocoderSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict


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
    try:
        code = sandbox.get_changed_code(include_signature=True)
        sandbox.copy_changed_code()
        test_result['metadata']['1_copy_change_success'] = True
        test_result['metadata']['1_copy_change_code'] = code
    except Exception:
        logger.error('Error fetching changed code for this instance')
        test_result['metadata']['1_copy_change_success'] = False
        test_result['metadata']['1_copy_change_code'] = None

    exit_code, output = sandbox.execute_and_check(
        'cd /testing',
        'Failed to cd /testing',
    )
    logger.info(f'cd $REPO_PATH: {output}')

    exit_code, output = sandbox.execute_and_check(
        'whoami',
        'Failed to run whoami',
    )
    logger.info(f'whoami: {output}')

    exit_code, output = sandbox.execute(
        '/home/devin/mambaforge/bin/mamba run -n test python3 /testing/start_test_opendevin.py'
    )
    logger.info(f'$TEST_CMD:\n{output}')

    exit_code, output = sandbox.execute_and_check(
        'cat /testing_files/results_biocoder.json', 'Failed to read the result file'
    )
    if exit_code == 0:
        test_result['metadata']['2_run_test_success'] = True
        test_result['metadata']['2_run_test_result'] = str(output)
    else:
        test_result['metadata']['2_run_test_success'] = False
        test_result['metadata']['2_run_test_result'] = str(output)
    json_obj = json.loads(output)
    test_result['result'] = json_obj['result']

    return test_result


def process_instance(
    instance,
    agent_class,
    metadata,
    skip_workspace_mount,
    eval_output_dir,
    reset_logger: bool = True,
):
    instance = BiocoderData(**instance)
    print(instance)
    workspace_dir_name = (
        f'{instance.repository}__{instance.test_case_id[:10]}__{os.getpid()}'.replace(
            '/', '__'
        )
    )
    workspace_mount_path = os.path.join(config.workspace_base, workspace_dir_name)
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
            eval_output_dir, 'logs', f'instance_{instance.test_case_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance.test_case_id}.\nHint: run "tail -f {log_file}" to see live logs in a seperate shell'
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

    # NOTE: this is something special we do for SWE-Bench due to the reason described in the previous section
    # You can omit this if you don't need to setup specialized sandbox
    workspace_dir_name = f'{instance.repository}__{instance.test_case_id[:10]}'.replace(
        '/', '__'
    )
    sandbox = BiocoderSSHBox.get_box_for_instance(
        instance,
        workspace_dir_name,
        skip_workspace_mount=False,
        workspace_mount_path=workspace_mount_path,
        sandbox_plugins=agenthub.Agent.get_cls(agent_class).sandbox_plugins,
    )

    sandbox.remove_code()

    # Prepare instruction
    instruction = (
        f'Please complete the function "{instance.signature}" in the file /workspace/{instance.repository.split("/")[1]}/{instance.filePath}.\n'
        f'The environment has been set up for you to start working. You may assume all necessary tools are installed.\n'
        f'To complete the task, you must directly modify the file and fill in the function, keeping in mind that the function signature is on line {instance.lineStart-1}\n\n'
        f'The function should do the following:\n'
        f'{instance.promptSummaryOnly}\n\n'
    )

    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        'You should NOT modify any other files other than the file intended. This means that you should NOT write any test cases.\n'
        'You may need context from other files in the repository to complete this task.'
        'Do NOT add any import statements or change anything else other than the writing the function body.\n'
        'You do not need to run the code to check if it works. \n'
        'Make sure to include proper formatting in Java and Python, including correct braces and/or indentation.\n'
    )

    # instruction = (
    #     f'In the file {instance.filePath}, there is a function with a signature and without a body. Your job is to complete the function, according to the given instructions. When you complete the function, respond with the function body, and nothing else.'
    #     'The repository has cloned for you to start working. You are not allowed to run any bash commands, just modify the files. \n\n'
    #     '# Problem Statement\n'
    #     'Complete the following function signature:\n\n'
    #     f'{instance.signature}'
    #     'The function should do the following:\n\n'
    #     f'{instance.promptSummaryOnly}\n\n'
    # )
    #
    # instruction += (
    #     'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
    #     'You should NOT modify any other files other than the file intended. This means that you should NOT write any test cases.\n'
    #     'Do NOT add any import statements or change anything else other than the writing the function body.\n'
    #     'You do not need to run the code to check if it works. The system will automatically check the correctness of your code.\n'
    #     'Make sure to include proper formatting in Java and Python, including correct braces and/or indentation.\n'
    # )

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

    test_result = get_test_result(instance, sandbox, workspace_dir_name)

    if state is None:
        raise ValueError('State should not be None.')
    metrics = state.metrics.get() if state.metrics else None

    # Save the output
    output = {
        'test_case_id': instance.test_case_id,
        'biocoder_instance': instance.to_dict(),
        'instruction': instruction,
        'generated': test_result['metadata']['1_copy_change_code'],
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


if __name__ == '__main__':
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset('lilbillbiscuit/biocoder_public')
    biocoder_tests = dataset['test'].to_pandas()

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
        'biocoder',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )

    eval_output_dir = str(eval_output_dir)

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
        biocoder_tests = biocoder_tests.head(eval_n_limit)
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_test_case_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_test_case_ids.add(data['test_case_id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_test_case_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_biocoder_tests = []
    for idx, instance in biocoder_tests.iterrows():
        if instance.test_case_id in finished_test_case_ids:
            logger.info(
                f'Skipping instance {instance.test_case_id} as it is already finished.'
            )
            continue
        new_biocoder_tests.append(instance)

    biocoder_tests = pd.DataFrame(new_biocoder_tests)
    logger.info(
        f'Finished instances: {len(finished_test_case_ids)}, Remaining instances: {len(biocoder_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(biocoder_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["test_case_id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]}')
        logger.info(
            f'Finished evaluation for instance {output["test_case_id"]}: {output["test_result"]}'
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
            for row_idx, instance in biocoder_tests.iterrows():
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
