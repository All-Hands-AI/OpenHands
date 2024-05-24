import asyncio
import json
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Dict

from datasets import load_dataset

from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
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


def get_opendevin_config():
    parser = get_parser()
    args, _ = parser.parse_known_args()
    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    return config


def get_sandbox(config):
    sandbox = DockerSSHBox(image=config.DOCKER_IMAGE, container_name='sandbox')
    return sandbox


def parse_eval_output(output: str) -> Dict[str, float]:
    metrics = {}
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':')
            try:
                metrics[key.strip()] = float(value.strip())
            except ValueError:
                logger.warning(f'Unable to parse metric value as float: {line}')
    return metrics


def process_instance(instance, agent_class, metadata, eval_output_dir):
    # Get the OpenDevin config
    config = get_opendevin_config()

    # Create a sandbox
    sandbox = get_sandbox(config)

    # Clone the task repo into the sandbox
    repo_url = instance['github']
    repo_name = repo_url.split('/')[-1]
    sandbox.exec(f'git clone {repo_url} /workspace/{repo_name}')
    sandbox.exec(f'chmod -R 777 /workspace/{repo_name}')

    # Navigate to the task's code path
    task_path = os.path.join('/workspace', repo_name, instance['path'])
    sandbox.exec(f'cd {task_path}')

    # Prepare the task instruction
    instruction = (
        f'Please complete the Machine Learning task in the following repository: {repo_url}\n\n'
        f'The task is: {instance["task"]}\n\n'
        f'{instance["instruction"]}\n\n'
        'You should only modify files under the specified path in the repo.\n'
        f'You can find the task repo at: {instance['path']}\n'
        'Here is the prefix code for the task:'
        '```python\n'
        f'{instance["prefix_code"]}\n'
        '```\n'
        'You should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).'
    )
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

    # Run the agent
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
            sandbox=sandbox,
        )
    )

    # Evaluate the agent's changes
    eval_cmd = instance['output']
    logger.info(f'Running evaluation command: {eval_cmd}')

    try:
        exit_code, eval_output = sandbox.exec(eval_cmd)
    except Exception as e:
        logger.error(f'Error running evaluation command: {e}')
        exit_code = -1
        eval_output = ''

    if exit_code != 0:
        logger.warning(f'Evaluation command failed with exit code {exit_code}')
        logger.warning(f'Output: {eval_output}')
        metrics = {}
    else:
        metrics = parse_eval_output(eval_output)
        logger.info(f'Evaluation metrics: {metrics}')

    # Save the output
    output = {
        'instance_id': instance['id'],
        'repo': repo_url,
        'instruction': instruction,
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'eval_exit_code': exit_code,
        'eval_output': eval_output,
        'metrics': metrics,
    }

    # Shutdown the sandbox
    sandbox.close()

    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '-s',
        '--data-split',
        type=str,
        default='full',
        choices=['full', 'quarter'],
        help='data split to evaluate on, either full or quarter',
    )
    args, _ = parser.parse_known_args()

    data_split = args.data_split
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
    ml_bench = load_dataset('DanielShao/ml-bench')

    eval_output_dir = f'evaluation/ml_bench/eval_output_{data_split}'
    os.makedirs(eval_output_dir, exist_ok=True)
    os.makedirs(os.path.join(eval_output_dir, 'logs'), exist_ok=True)

    model_name = config.llm.model.split('/')[-1]

    metadata = {
        'agent_class': agent_class,
        'model_name': model_name,
        'data_split': data_split,
        'num_workers': num_workers,
    }

    logger.info(f'Using evaluation output directory: {eval_output_dir}')
    logger.info(f'Evaluating on data split: {data_split}')
    logger.info(f'Using {num_workers} worker processes')

    output_file = os.path.join(eval_output_dir, f'results_{data_split}.jsonl')
    logger.info(f'Writing results to {output_file}')

    with open(output_file, 'w') as f:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            for instance in ml_bench[data_split]:
                future = executor.submit(
                    process_instance, instance, agent_class, metadata, eval_output_dir
                )
                futures.append(future)

            for future in futures:
                try:
                    output = future.result()
                    f.write(json.dumps(output) + '\n')
                    logger.info(f'Finished instance {output["instance_id"]}')
                except Exception as e:
                    logger.exception(f'Error processing instance: {e}')

    logger.info('Evaluation completed.')
