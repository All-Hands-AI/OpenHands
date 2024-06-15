import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import re
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

import huggingface_hub
from datasets import load_dataset
from tqdm import tqdm

from evaluation.gaia.scorer import question_scorer
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import CmdRunAction, MessageAction
from opendevin.events.serialization.event import event_to_dict

DATASET_CACHE_DIR = '~/.cache/open-devin/evals/gaia'
DATASET_CACHE_DIR = os.path.expanduser(DATASET_CACHE_DIR)


def cleanup():
    logger.info('Cleaning up child processes...')
    for process in mp.active_children():
        logger.info(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please first send your answer to user through message and then <execute_bash> exit </execute_bash>.\n'
        'Please encapsulate your final answer (answer ONLY) within <solution> and </solution>.\n'
        'For example: The answer to the question is <solution> 42 </solution>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP.\n'
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
    'CodeActAgent': 'When you think you have solved the question, please first send your answer to user through message and then exit.\n'
}


def process_instance(instance, agent_class, metadata, reset_logger: bool = True):
    # create process-specific workspace dir
    # we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    old_workspace_mount_path = config.workspace_mount_path
    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)
    config.workspace_mount_path = workspace_mount_path

    # Setup the logger properly, so you can run multi-processing to parallize the evaluation
    eval_output_dir = metadata['eval_output_dir']
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            eval_output_dir, 'logs', f'instance_{instance["task_id"]}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance["task_id"]}.\nLOG:   tail -f {log_file}'
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
    if instance['file_name'] != '':
        # if this question comes with a file, we need to save it to the workspace
        src_file = os.path.join(
            DATASET_CACHE_DIR, '2023', metadata['data_split'], instance['file_name']
        )
        extension_name = instance['file_name'].split('.')[-1]
        dest_file = os.path.join(workspace_mount_path, f'file.{extension_name}')
        shutil.copyfile(src_file, dest_file)
        logger.info(f'File copied to {dest_file}')
    else:
        dest_file = None

    # Prepare instruction
    instruction = f"{instance['Question']}\n"
    logger.info(f'Instruction: {instruction}')
    if dest_file:
        instruction += f"\n\nThe mentioned file is provided in the workspace at: {dest_file.split('/')[-1]}"

    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
    instruction += 'Please encapsulate your final answer (answer ONLY) within <solution> and </solution>.\n'
    instruction += (
        'For example: The answer to the question is <solution> 42 </solution>.\n'
    )
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')
    logger.info(f'Instruction:\n{instruction}', extra={'msg_type': 'OBSERVATION'})

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
        )
    )
    # ======= Attempt to evaluate the agent's edits =======
    # If you are working on simplier benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    model_answer_raw = ''
    for act, _ in reversed(state.history):
        if isinstance(act, CmdRunAction) and act.source == 'agent':
            model_answer_raw = act.thought
            break
        elif isinstance(act, MessageAction) and act.source == 'agent':
            model_answer_raw = act.content
            break

    # attempt to parse model_answer
    model_answer = re.findall(r'<solution>(.*?)</solution>', model_answer_raw)
    if len(model_answer) == 0:
        logger.warning(f'Failed to parse model answer: {model_answer_raw}')
        model_answer = model_answer_raw
    else:
        model_answer = model_answer[0]

    logger.info(
        f'Final message: {model_answer} | Ground truth: {instance["Final answer"]}'
    )
    score = question_scorer(
        model_answer=model_answer, ground_truth=instance['Final answer']
    )
    test_result = {
        'score': score,
        'model_answer_raw': model_answer_raw,
        'model_answer': model_answer,
        'ground_truth': instance['Final answer'],
    }

    # Save the output
    output = {
        'instance_id': instance['task_id'],
        'instance': instance,
        'instruction': instance['Question'],
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'error': state.error if state and state.error else None,
        'test_result': test_result,
    }

    # Close the sandbox
    config.workspace_mount_path = old_workspace_mount_path
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--level',
        type=str,
        help='gaia level to evaluate, eg. 2023_level1',
    )
    parser.add_argument(
        '--data-split',
        type=str,
        help='data split to evaluate, eg. validation',
    )
    args, _ = parser.parse_known_args()
    if args.directory:
        config.workspace_base = os.path.abspath(args.directory)
        logger.info(f'Setting workspace base to {config.workspace_base}')
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    level = args.level
    data_split = args.data_split
    dataset = load_dataset('gaia-benchmark/GAIA', level)
    huggingface_hub.snapshot_download(
        'gaia-benchmark/GAIA',
        repo_type='dataset',
        local_dir=DATASET_CACHE_DIR,
    )
    gaia_tests = dataset[data_split]
    logger.info(f'Evaluating GAIA-Benchmark {level} {data_split} split')

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
        'gaia',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )

    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_dir, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    metadata = {
        'gaia-level': level,
        'data_split': data_split,
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
        gaia_tests = gaia_tests.select(list(range(eval_n_limit)))
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_task_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_task_ids.add(data['instance_id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_task_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_gaia_tests = []
    for instance in gaia_tests:
        if instance['task_id'] in finished_task_ids:
            logger.info(
                f'Skipping instance {instance["task_id"]} as it is already finished.'
            )
            continue
        new_gaia_tests.append(instance)

    gaia_tests = new_gaia_tests
    logger.info(
        f'Finished instances: {len(finished_task_ids)}, Remaining instances: {len(gaia_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(gaia_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["instance_id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["score"]}')
        logger.info(
            f'Finished evaluation for instance {output["instance_id"]}: {output["test_result"]}'
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
            for instance in gaia_tests:
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
                    reset_logger=bool(num_workers > 1),
                )
                future.add_done_callback(update_progress)
                futures.append(future)

            # Wait for all futures to complete
            for future in futures:
                future.result()
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt received. Cleaning up...')
        cleanup()

    output_fp.close()
    logger.info('Evaluation finished.')
