import json
import multiprocessing as mp
import os
import pathlib
import subprocess
import time
from asyncio.log import logger
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable

import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm

from opendevin.controller.state.state import State
from opendevin.core.config import LLMConfig
from opendevin.events.action import Action
from opendevin.events.action.message import MessageAction


class EvalMetadata(BaseModel):
    agent_class: str
    llm_config: LLMConfig
    max_iterations: int
    eval_output_dir: str
    start_time: str
    git_commit: str
    dataset: str | None = None
    data_split: str | None = None
    details: dict[str, Any] | None = None

    def model_dump_json(self, *args, **kwargs):
        dumped = super().model_dump_json(*args, **kwargs)
        dumped_dict = json.loads(dumped)
        logger.debug(f'Dumped metadata: {dumped_dict}')
        # avoid leaking sensitive information
        dumped_dict['llm_config'] = self.llm_config.to_safe_dict()
        return json.dumps(dumped_dict)


def codeact_user_response(
    state: State,
    encapsulate_solution: bool = False,
    try_parse: Callable[[Action], str] | None = None,
) -> str:
    encaps_str = (
        (
            'Please encapsulate your final answer (answer ONLY) within <solution> and </solution>.\n'
            'For example: The answer to the question is <solution> 42 </solution>.\n'
        )
        if encapsulate_solution
        else ''
    )
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please first send your answer to user through message and then <execute_bash> exit </execute_bash>.\n'
        f'{encaps_str}'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP.\n'
    )

    if state.history:
        # check if the last action has an answer, if so, early exit
        if try_parse is not None:
            last_action = state.history.get_last_action()
            ans = try_parse(last_action)
            if ans is not None:
                return '/exit'

        # check if the agent has tried to talk to the user 3 times, if so, let the agent know it can give up
        user_msgs = [
            event
            for event in state.history.get_events()
            if isinstance(event, MessageAction) and event.source == 'user'
        ]
        if len(user_msgs) >= 2:
            # let the agent know that it can give up when it has tried 3 times
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def make_metadata(
    llm_config: LLMConfig,
    dataset_name: str,
    agent_class: str,
    max_iterations: int,
    eval_note: str | None,
    eval_output_dir: str,
    data_split: str | None = None,
    details: dict[str, Any] | None = None,
) -> EvalMetadata:
    model_name = llm_config.model.split('/')[-1]
    eval_note = f'_N_{eval_note}' if eval_note else ''

    eval_output_path = os.path.join(
        eval_output_dir,
        dataset_name,
        agent_class,
        f'{model_name}_maxiter_{max_iterations}{eval_note}',
    )

    pathlib.Path(eval_output_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_path, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_path}')

    metadata = EvalMetadata(
        agent_class=agent_class,
        llm_config=llm_config,
        max_iterations=max_iterations,
        eval_output_dir=eval_output_path,
        start_time=time.strftime('%Y-%m-%d %H:%M:%S'),
        git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        .decode('utf-8')
        .strip(),
        dataset=dataset_name,
        data_split=data_split,
        details=details,
    )
    metadata_json = metadata.model_dump_json()
    logger.info(f'Metadata: {metadata_json}')
    with open(os.path.join(eval_output_path, 'metadata.json'), 'w') as f:
        f.write(metadata_json)

    return metadata


def prepare_dataset(dataset: pd.DataFrame, output_file, eval_n_limit, id_column):
    logger.info(f'Writing evaluation output to {output_file}')
    finished_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_ids.add(data[id_column])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_ids)} finished instances.'
        )

    if eval_n_limit:
        dataset = dataset.head(eval_n_limit)
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    new_dataset = [
        instance
        for _, instance in dataset.iterrows()
        if instance[id_column] not in finished_ids
    ]
    logger.info(
        f'Finished instances: {len(finished_ids)}, Remaining instances: {len(new_dataset)}'
    )

    return pd.DataFrame(new_dataset)


def run_evaluation(
    dataset: pd.DataFrame,
    metadata: EvalMetadata,
    output_file: str,
    num_workers: int,
    process_instance_func: Callable[[pd.Series, EvalMetadata, bool], Any],
    id_column: str,
):
    logger.info(
        f'Evaluation started with Agent {metadata.agent_class}, '
        f'model {metadata.llm_config.model}, max iterations {metadata.max_iterations}.'
    )
    pbar = tqdm(total=len(dataset))
    output_fp = open(output_file, 'a')

    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output[id_column]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        logger.info(
            f'Finished evaluation for instance {output[id_column]}: {output["test_result"]["result"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            for _, instance in dataset.iterrows():
                future = executor.submit(
                    process_instance_func,
                    instance,
                    metadata,
                    bool(num_workers > 1),
                )
                future.add_done_callback(update_progress)
                futures.append(future)

            for future in futures:
                future.result()
    except KeyboardInterrupt:
        print('KeyboardInterrupt received. Cleaning up...')
        cleanup()

    output_fp.close()
    logger.info('Evaluation finished.')
