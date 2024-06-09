import asyncio
import json
import logging
import os
import pathlib
import subprocess
import time

import browsergym.webarena  # noqa F401 register webarena tasks as gym environments
import gymnasium as gym
from tqdm import tqdm

from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.serialization.event import event_to_dict
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.tools import RuntimeTool

SUPPORTED_AGENT_CLS = {'BrowsingAgent'}


def process_instance(
    env_id: str,
    metadata: dict,
    eval_output_dir: str,
    docker_sandbox: DockerSSHBox,
    reset_logger: bool = True,
):
    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(eval_output_dir, 'logs', f'instance_{env_id}.log')
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {env_id}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
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
        logger.info(f'Starting evaluation for instance {env_id}.')

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    runtime_tools_config = {
        RuntimeTool.BROWSER: {
            'browsergym_eval': env_id,
            'browsergym_eval_save_dir': eval_output_dir,
        }
    }

    state: State = asyncio.run(
        main(
            'PLACEHOLDER_GOAL',
            runtime_tools_config=runtime_tools_config,
            sandbox=docker_sandbox,
        )
    )

    # ======= Attempt to evaluate the agent's environment impact =======

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    metrics = state.metrics.get() if state.metrics else None
    browsergym_eval_dir = os.path.join(eval_output_dir, env_id.split('/')[1])
    # read goal
    with open(
        os.path.join(browsergym_eval_dir, 'goal.txt'), 'r', encoding='utf-8'
    ) as f:
        instruction = f.read()
    # read reward
    with open(
        os.path.join(browsergym_eval_dir, 'rewards.json'), 'r', encoding='utf-8'
    ) as f:
        rewards = json.load(f)
        reward = max(rewards)

    # Save the output
    output = {
        'instance_id': env_id,
        'instruction': instruction,
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'metrics': metrics,
        'error': state.error if state and state.error else None,
        'test_result': reward,
    }

    return output


if __name__ == '__main__':
    env_ids = [
        id for id in gym.envs.registry.keys() if id.startswith('browsergym/webarena')
    ]

    # Check https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/README.md#configure-opendevin-and-your-llm
    # for details of how to set `llm_config`
    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    logger.info(f'Config for evaluation: {config}')

    # TEST METADATA
    agent_class = args.agent_cls
    assert agent_class in SUPPORTED_AGENT_CLS, f'Unsupported agent class: {agent_class}'
    model_name = config.llm.model.split('/')[-1]
    max_iterations = args.max_iterations
    eval_note = ''
    if args.eval_note is not None:
        eval_note += '_N_' + args.eval_note
    eval_output_dir = os.path.join(
        args.eval_output_dir,
        'webarena',
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
        # get the commit id of current repo for reproducibility
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
        env_ids = env_ids[:eval_n_limit]
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
    new_env_ids = []
    for idx in env_ids:
        if idx in finished_instance_ids:
            logger.info(f'Skipping instance {idx} as it is already finished.')
            continue
        new_env_ids.append(idx)

    env_ids = new_env_ids
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(env_ids)}'
    )

    # =============================================

    docker_sandbox = DockerSSHBox()
    for env_id in tqdm(env_ids):
        try:
            output = process_instance(
                env_id=env_id,
                metadata=metadata,
                eval_output_dir=eval_output_dir,
                docker_sandbox=docker_sandbox,
                reset_logger=False,
            )
            output_fp.write(json.dumps(output) + '\n')
            output_fp.flush()
        except Exception as e:
            logger.error(f'Error processing instance {env_id}: {e}')

    output_fp.close()
    logger.info('Evaluation finished.')
