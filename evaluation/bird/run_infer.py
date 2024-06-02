import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import re
import shutil
import sqlite3
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
from datasets import load_dataset
from func_timeout import FunctionTimedOut, func_timeout
from tqdm import tqdm

from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict


def cleanup():
    logger.info('Cleaning up child processes...')
    for process in mp.active_children():
        logger.info(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have completed the SQL, please run the following command: <execute_bash> exit </execute_bash>.\n'
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


def execute_sql(db_path, gen_sql, gold_sql):
    """
    Execute the generated SQL and the ground truth SQL and compare the results.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(gen_sql)
        predicted_res = cursor.fetchall()
        cursor.execute(gold_sql)
        ground_truth_res = cursor.fetchall()
        res = 0
        if set(predicted_res) == set(ground_truth_res):
            res = 1
    return res


def get_test_result(instance, path, timeout=30):
    test_result = {'result': {}, 'metadata': {}}

    # Read the generated python file
    with open(path, 'r') as f:
        gen_file = f.read()

    # Extract the SQL from the python file
    gen_sql = ''
    pattern = r'sql\s*=\s*"([^"]+)"'
    match = re.search(pattern, gen_file)
    if match:
        gen_sql = match.group(1)
    else:
        print('No match found.')

    gold_sql = instance.SQL
    # Execute the SQL
    try:
        res = func_timeout(
            timeout, execute_sql, args=(instance.db_path, gen_sql, gold_sql)
        )
        status = 'success'
    except FunctionTimedOut:
        res = 0
        status = 'timeout'
    except Exception as e:
        res = 0
        status = 'error'
        logger.error(f'Error: {e}')

    # Save the test result
    test_result['result'] = {'passed': res, 'status': status}
    test_result['metadata'] = {
        'timeout': timeout,
        'gen_sql': gen_sql,
        'gold_sql': gold_sql,
    }
    return test_result


def process_instance(
    instance, agent_class, metadata, skip_workspace_mount, reset_logger: bool = True
):
    workspace_mount_path = os.path.join(
        config.workspace_mount_path, 'bird_eval_workspace'
    )
    # create process-specific workspace dir
    # if `not skip_workspace_mount` - we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    if not skip_workspace_mount:
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # reset workspace to config
    config.workspace_mount_path = workspace_mount_path

    # Copy the database to the workspace
    db_root = os.path.join(
        config.workspace_base, 'evaluation_bird/dev/dev_databases', instance.db_id
    )
    target_path = os.path.join(workspace_mount_path, f'{instance.db_id}')
    if not os.path.exists(target_path):
        logger.info(f'Copying database from {db_root} to {target_path}...')
        shutil.copytree(db_root, target_path)

    # Set up the database path
    database_path = os.path.join(instance.db_id, f'{instance.db_id}.sqlite')

    # Set up the logger properly, so you can run multi-processing to parallelize the evaluation
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

    # Create file with BIRD instance
    statements = f"""
    import sqlite3
    def execute_sql(db_path, sql):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            return result

    if __name__ == '__main__':
        sql = "" # fill in your SQL here
        db_path = "{database_path}"
        print(db_path)
        result = execute_sql(db_path, sql)
        print(result)
    """
    path = os.path.join(
        config.workspace_mount_path, f'{instance.task_id.replace("/", "__")}.py'
    )
    instruction = (
        f'You are a SQL expert and need to complete the following text-to-SQL tasks.'
        f'\n\n{instance.instruction}\n\n'
        'Please write the SQL in one line without line breaks.'
        f'And write a new python file named {instance.task_id.replace("/", "__")}.py to call the SQL you wrote.'
        'You need to follow the code template below:'
        f'\n\n{statements}\n\n'
        'Environment has been set up for you to start working.'
        'You may assume all necessary tools are installed.\n\n'
    )
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
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
    metrics = state.metrics.get() if state.metrics else None

    # Save the output
    output = {
        'task_id': instance.task_id,
        'instruction': instruction,
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'metrics': metrics,
        'error': state.error if state and state.error else None,
        'test_result': test_result,
    }
    return output


def load_bird():
    """
    Main function to handle the flow of downloading, processing, and loading the bird dataset.
    """
    raw_dataset_path = download_bird()
    bird_dataset = process_bird(raw_dataset_path)
    return bird_dataset


def download_bird():
    """
    Downloads and extracts the bird dataset from a specified URL into a local directory.
    """
    dataset_path = os.path.join(config.workspace_base, 'evaluation_bird')
    devset_path = os.path.join(dataset_path, 'dev')
    if not os.path.exists(dataset_path):
        logger.info(
            f'{dataset_path} folder does not exist, starting download and extraction...'
        )
        os.makedirs(dataset_path, exist_ok=True)
        download_url = 'https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip'
        download_path = os.path.join(dataset_path, 'dev.zip')
        logger.info('Start Downloading...')
        subprocess.run(['wget', download_url, '-O', download_path])
        logger.info('Download completed.')
        logger.info('Start Extracting...')
        subprocess.run(['unzip', download_path, '-d', dataset_path])
        # extract databases
        devset_path = os.path.join(dataset_path, 'dev')
        database_path = os.path.join(devset_path, 'dev_databases.zip')
        subprocess.run(['unzip', database_path, '-d', devset_path])
        logger.info('Extraction completed.')
    else:
        logger.info(f'{dataset_path} folder already exists.')
    return devset_path


def process_bird(dataset_path):
    """
    Processes the raw bird dataset into a structured format and saves it as JSON.
    """
    processed_path = os.path.join(dataset_path, 'processed_dev.json')
    if not os.path.exists(processed_path):
        logger.info(f'{processed_path} folder does not exist, starting processing...')
        raw_data_path = os.path.join(dataset_path, 'dev.json')
        database_path = os.path.join(dataset_path, 'dev_databases')
        processed_data = []
        with pathlib.Path(raw_data_path).open('r') as f:
            data = json.load(f)
            for e in tqdm(data):
                item = {
                    'task_id': f'{len(processed_data)}',
                    'db_path': os.path.join(
                        database_path, e['db_id'], f"{e['db_id']}.sqlite"
                    ),
                    'db_id': e['db_id'],
                    'instruction': create_prompt(e, database_path),
                    'SQL': e['SQL'],
                }
                processed_data.append(item)

        with pathlib.Path(processed_path).open('w') as f:
            json.dump(processed_data, f, indent=2)
            logger.info(f'Processed data saved to {processed_path}')
    else:
        logger.info(f'{processed_path} folder already exists.')
    bird_dataset = load_dataset('json', data_files={'test': processed_path})
    return bird_dataset


def extract_create_table_prompt(db_path, limit_value=0):
    """
    Generates a SQL prompt with CREATE TABLE statements and sample data from the database.
    """
    table_query = "SELECT * FROM sqlite_master WHERE type='table';"
    tables = sqlite3.connect(db_path).cursor().execute(table_query).fetchall()
    prompt = ''
    for table in tables:
        table_name = table[1]
        create_table_statement = table[-1]

        table_info_query = f'PRAGMA table_info(`{table_name}`);'
        top_k_row_query = f'SELECT * FROM {table_name} LIMIT {limit_value};'
        try:
            headers = [
                x[1]
                for x in sqlite3.connect(db_path)
                .cursor()
                .execute(table_info_query)
                .fetchall()
            ]
        except Exception:
            logger.error(f'Error Connection: {table_info_query}, {top_k_row_query}')
            exit(0)

        prompt += create_table_statement + ';\n'
        if limit_value > 0:
            top_k_rows = (
                sqlite3.connect(db_path).cursor().execute(top_k_row_query).fetchall()
            )
            prompt += (
                f"/*\n3 example rows:\n{top_k_row_query}\n{'    '.join(headers)}\n"
            )
            for row in top_k_rows:
                row = [str(x) for x in row]
                row = [x if x is not None else '' for x in row]
                prompt += '    '.join(row) + '\n'
            prompt += '*/\n'
        prompt += '\n'
    return prompt


def create_prompt(e, database_path):
    """
    Create a prompt for the given example
    """
    db_id = e['db_id']
    db_path = pathlib.Path(database_path) / db_id / f'{db_id}.sqlite'

    # Extract the CREATE TABLE statements and sample data from the database
    prompt = extract_create_table_prompt(db_path)
    prompt += f"-- External Knowledge: {e['evidence']}\n\n"
    prompt += '-- Using valid SQLite and understanding External Knowledge, answer the following questions for the tables provided above.\n\n'
    prompt += '-- Using valid SQLite, answer the following questions for the tables provided above.\n'
    prompt += f"Question: {e['question']}\n"

    return prompt


if __name__ == '__main__':
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    # Due to the large size of the BIRD database, it cannot be hosted on huggingface datasets, so it needs to be downloaded
    bird_dataset = load_bird()
    bird_tests = bird_dataset['test'].to_pandas()

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
        'bird',
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
        bird_tests = bird_tests.head(eval_n_limit)
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
    new_bird_tests = []
    for idx, instance in bird_tests.iterrows():
        if instance.task_id in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance.task_id} as it is already finished.'
            )
            continue
        new_bird_tests.append(instance)

    bird_tests = pd.DataFrame(new_bird_tests)
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(bird_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(bird_tests))

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
            for row_idx, instance in bird_tests.iterrows():
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
