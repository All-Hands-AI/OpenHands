"""
Implements evaluation of agents on ML-Bench, a benchmark for assessing the effectiveness of
Large Language Models (LLMs) in leveraging existing functions in open-source libraries for
machine learning tasks. The benchmark is introduced in the paper "ML-Bench: Evaluating Large
Language Models for Code Generation in Repository-Level Machine Learning Tasks"
(https://arxiv.org/abs/2311.09835).

Please see https://ghcr.io/super-dainiu/ml_bench and https://huggingface.co/datasets/super-dainiu/ml-bench
for more details on the dataset and docker image used in this evaluation script.

TODOs:
- Support additional evaluation settings, such as providing raw README content or using a
  retriever to extract relevant segments.
- Clean up the code and docker image used for evaluation.
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

from datasets import load_dataset
from tqdm import tqdm

from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict
from opendevin.runtime.docker.ssh_box import DockerSSHBox


def cleanup():
    logger.info('Cleaning up child processes...')
    for process in mp.active_children():
        logger.info(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have completed the task, please run the following command: <execute_bash> exit </execute_bash>.\n'
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
    'CodeActAgent': 'When you think you have completed the task, please run the following command: <execute_bash> exit </execute_bash>.\n'
}

ID2CONDA = {
    1: 'dgl_DS',
    2: 'bert_DS',
    3: 'lavis_DS',
    4: 'if_DS',
    5: 'V2V_DS',
    6: 'esm_DS',
    7: 'OP_DS',
    8: 'TSL_DS',
    9: 'EAP_DS',
    10: 'PG_DS',
    11: 'PIM_DS',
    12: 'AD2_DS',
    13: 'L3_DS',
    14: 'MZ2_DS',
    15: 'GSA2_DS',
}


def process_instance(
    instance, agent_class, metadata, eval_output_dir, reset_logger: bool = True
):
    old_workspace_mount_path = config.workspace_mount_path
    old_workspace_base = config.workspace_base
    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        # create process-specific workspace dir
        # so that different agent don't interfere with each other.
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

        # reset workspace to config
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                eval_output_dir,
                'logs',
                f"instance_{instance['id']}_pid_{os.getpid()}.log",
            )
            # Remove all existing handlers from logger
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # add back the console handler to print ONE line
            logger.addHandler(get_console_handler())
            logger.info(
                f"Starting evaluation for instance {instance['id']}.\nLOG:   tail -f {log_file}"
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

        # Create a sandbox, using the instance ID as the session ID to avoid conflicts
        sandbox = DockerSSHBox(sid=str(instance['id']) + '_' + str(os.getpid()))

        # Set up the task environment
        sandbox.execute(f'conda activate {ID2CONDA[instance["github_id"]]}')

        # Clone the task repo into the sandbox
        repo_url = instance['github']
        repo_name = repo_url.split('/')[-1]
        sandbox.execute(f'git clone {repo_url} /workspace/{repo_name}')
        sandbox.execute(f'chmod -R 777 /workspace/{repo_name}')

        # Navigate to the task's code path
        task_path = os.path.join('/workspace', repo_name, instance['path'][2:])
        sandbox.execute(f'cd {task_path}')

        # Prepare the task instruction
        instruction = (
            f'Please complete the Machine Learning task in the following repository: {repo_name}\n\n'
            f'The task is: {instance["task"]}\n\n'
            f'{instance["instruction"]}\n\n'
            'You should create a script named `run.sh` under the specified path in the repo to run the task.\n\n'
            f'You can find the task repo at: {task_path}\n\n'
            + (
                'Here is the prefix code for the task:\n'
                '```bash\n'
                f'{instance["prefix_code"]}\n'
                '```\n\n'
                if instance['prefix_code']
                else ''
            )
            + 'You should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).'
        )
        instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

        # Run the agent
        state: State = asyncio.run(
            main(
                instruction,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                    agent_class
                ),
                sandbox=sandbox,
            )
        )
        metrics = state.metrics.get() if state.metrics else {}

        # Evaluate the agent's script
        eval_script = os.path.join(task_path, 'run.sh')
        logger.info(f'Running evaluation script: {eval_script}')

        try:
            _, eval_script_content = sandbox.execute(f'cat {eval_script}')
        except Exception as e:
            logger.error(f'Error reading evaluation script: {e}')
            eval_script_content = ''

        try:
            exit_code, eval_output = sandbox.execute(
                f'timeout 120s conda run -n {ID2CONDA[instance["github_id"]]} bash {eval_script}',
                timeout=600,
            )
        except Exception as e:
            logger.error(f'Error running evaluation script: {e}')
            exit_code = -1
            eval_output = ''

        if exit_code != 0 and exit_code != 124:
            logger.warning(f'Evaluation script failed with exit code {exit_code}')
            logger.warning(f'Output: {eval_output}')
            metrics['success'] = int(
                'KeyboardInterrupt' in eval_output
            )  # super-dainiu: assume ``KeyboardInterrupt`` is a success as is done in ML-Bench
        else:
            logger.info(f'Evaluation script succeeded with exit code {exit_code}')
            logger.info(f'Output: {eval_output}')
            metrics['success'] = 1

        # Save the output
        output = {
            'instance_id': instance['id'],
            'repo': repo_url,
            'instruction': instruction,
            'metadata': metadata,
            'history': [
                (event_to_dict(action), event_to_dict(obs))
                for action, obs in state.history
            ],
            'eval_script': eval_script_content,
            'eval_exit_code': exit_code,
            'eval_output': eval_output,
            'metrics': metrics,
        }

    except Exception as e:
        logger.error(f'Error processing instance {instance["id"]}: {e}')
        raise
    finally:
        config.workspace_mount_path = old_workspace_mount_path
        config.workspace_base = old_workspace_base

    # Shutdown the sandbox
    sandbox.close()
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '-s',
        '--eval-split',
        type=str,
        default='quarter',
        choices=['full', 'quarter'],
        help='data split to evaluate on, either full or quarter',
    )
    args, _ = parser.parse_known_args()

    data_split = args.eval_split
    agent_class = args.agent_cls
    num_workers = args.eval_num_workers

    # Check https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/README.md#configure-opendevin-and-your-llm
    # for details of how to set `llm_config`
    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    logger.info(f'Config for evaluation: {config}')

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    ml_bench = load_dataset('super-dainiu/ml-bench', split=data_split).to_pandas()

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        ml_bench = ml_bench.head(eval_n_limit)
        logger.info(f'Limiting evaluation to {eval_n_limit} instances.')

    # TEST METADATA
    model_name = config.llm.model.split('/')[-1]
    max_iterations = args.max_iterations
    eval_note = ''
    if args.eval_note is not None:
        eval_note += '_N_' + args.eval_note
    eval_output_dir = os.path.join(
        args.eval_output_dir,
        'ml_bench',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )
    os.makedirs(eval_output_dir, exist_ok=True)
    os.makedirs(os.path.join(eval_output_dir, 'logs'), exist_ok=True)
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    metadata = {
        'agent_class': agent_class,
        'model_name': model_name,
        'max_iterations': max_iterations,
        'eval_output_dir': eval_output_dir,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        # get the commit id of current repo for reproducibility
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        .decode('utf-8')
        .strip(),
    }
    logger.info(f'Metadata: {metadata}')

    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Evaluating on data split: {data_split}')
    logger.info(f'Using {num_workers} worker processes')
    logger.info(f'Writing evaluation output to {output_file}')

    finished_instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    print(f'Error parsing line: {line}')
                finished_instance_ids.add(data['instance_id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_instance_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, data split {data_split}.'
    )

    # Filter out finished instances
    new_instances = [
        instance
        for _, instance in ml_bench.iterrows()
        if instance['id'] not in finished_instance_ids
    ]
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(new_instances)}'
    )

    pbar = tqdm(total=len(new_instances))

    # This function tracks the progress AND writes the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["instance_id"]}')
        pbar.set_postfix_str(f'Metrics: {output["metrics"]}')
        logger.info(
            f'Finished evaluation for instance {output["instance_id"]}: {output["metrics"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            for _, instance in enumerate(new_instances):
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
                    eval_output_dir,
                    reset_logger=bool(num_workers > 1),
                )
                future.add_done_callback(update_progress)
                futures.append(future)

            for future in futures:
                output = future.result()
    except KeyboardInterrupt:
        print('KeyboardInterrupt received. Cleaning up...')
        cleanup()

    logger.info('Evaluation completed.')
