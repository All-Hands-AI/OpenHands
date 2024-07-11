import asyncio
import json
import logging
import os

import browsergym.webarena  # noqa F401 register webarena tasks as gym environments
import gymnasium as gym
import pandas as pd

from evaluation.utils.shared import (
    EvalMetadata,
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, parse_arguments
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.tools import RuntimeTool

SUPPORTED_AGENT_CLS = {'BrowsingAgent'}


docker_ssh_box: DockerSSHBox | None = None


def get_sandbox():
    global docker_ssh_box
    if docker_ssh_box is None:
        docker_ssh_box = DockerSSHBox()
    return docker_ssh_box


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(llm_config=metadata.llm_config))
    env_id = instance.id
    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            metadata.eval_output_dir, 'logs', f'instance_{env_id}.log'
        )
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
            'browsergym_eval_save_dir': metadata.eval_output_dir,
        }
    }

    state: State | None = asyncio.run(
        run_agent_controller(
            agent,
            'PLACEHOLDER_GOAL',
            max_iterations=metadata.max_iterations,
            runtime_tools_config=runtime_tools_config,
            sandbox=get_sandbox(),
            sid=env_id,
        )
    )

    # ======= Attempt to evaluate the agent's environment impact =======

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    metrics = state.metrics.get() if state.metrics else None
    browsergym_eval_dir = os.path.join(metadata.eval_output_dir, env_id.split('/')[1])
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

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = state.history.compatibility_for_eval_history_pairs()

    # Save the output
    output = {
        'instance_id': env_id,
        'instruction': instruction,
        'metadata': metadata.model_dump(),
        'history': histories,
        'metrics': metrics,
        'error': state.last_error if state and state.last_error else None,
        'test_result': reward,
    }

    return output


if __name__ == '__main__':
    args = parse_arguments()

    env_ids = [
        id for id in gym.envs.registry.keys() if id.startswith('browsergym/webarena')
    ]

    dataset = pd.DataFrame(
        {
            'id': [
                id
                for id in gym.envs.registry.keys()
                if id.startswith('browsergym/miniwob')
            ]
        }
    )

    id_column = 'id'
    llm_config = get_llm_config_arg(args.llm_config) if args.llm_config else config.llm
    logger.info(f'Config for evaluation: {config}')

    metadata = make_metadata(
        llm_config,
        args.dataset_name,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(dataset, output_file, args.eval_n_limit, id_column)
    _ = get_sandbox()  # Initialize the sandbox
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
