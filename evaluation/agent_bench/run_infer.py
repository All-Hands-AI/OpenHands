import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

from huggingface_hub import snapshot_download
from tqdm import tqdm

from evaluation.agent_bench.helper import compare_results, get_check_method, get_post_cmd, get_pre_cmd, \
    get_retriv_agent_answer_cmd
from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict
from opendevin.runtime.docker.ssh_box import DockerSSHBox


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please first send your answer to user through message and then exit.\n'
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


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have solved the question, '
    'please first send your answer to user through message and then exit.\n'
}


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def process_instance(
    instance,
    agent_class,
    metadata,
    eval_output_dir,
    reset_logger: bool = True,
):
    # =============================================
    # preparation
    # =============================================

    inst_id = instance['instance_id']
    question = instance['description']

    # Set up the logger properly, so you can run multiprocessing to parallel the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(eval_output_dir, 'logs', f'instance_{inst_id}.log')
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {inst_id}.\nHint: run "tail -f {log_file}" to see live logs in a seperate shell'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

    # =============================================
    # build instruction
    # =============================================

    # Prepare instruction
    instruction = (
        f'Please fix the following issue.\n'
        'Environment has been set up for you to start working. You may assume all necessary tools are installed.\n\n'
        '# Problem \n'
        f'{question}\n\n'
    )
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided '
        'to you AND NEVER ASK FOR HUMAN HELP.\n'
    )
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

    # =============================================
    # create sandbox and run the agent
    # =============================================

    sandbox = DockerSSHBox()
    if config.is_mock:
        sandbox.start_ssh_session()

    # pre start
    pre_cmd = get_pre_cmd(instance)
    if pre_cmd != '':
        logger.info(f'Running pre stage script: {pre_cmd}')
        sandbox.execute(pre_cmd)

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    if config.is_mock:
        fake_state = State()
        act = MessageAction(content='Alice', wait_for_response=False)
        act._source = 'agent'
        fake_state.history = [
            (
                act,
                None,
            ),
        ]
        state = fake_state
    else:
        state: State = asyncio.run(
            main(
                instruction,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
                sandbox=sandbox,
            )
        )

    if state is None:
        raise ValueError('State should not be None.')

    # get the ground truth
    # OSBenchSSHBox.get_ground_truth(instance, state)

    # =============================================
    # result evaluation
    # =============================================

    # post end
    final_ans = ''
    post_cmd = get_post_cmd(instance)
    check_method = get_check_method(instance)
    if post_cmd != '':
        logger.info(f'Running post stage script: {post_cmd}')
        _, final_ans = sandbox.execute(post_cmd)

    agent_answer = ''
    retriv_agent_answer_cmd = get_retriv_agent_answer_cmd(instance)
    if retriv_agent_answer_cmd != '':
        logger.info(f'Running retriv agent answer script: {retriv_agent_answer_cmd}')
        _, agent_answer = sandbox.execute(retriv_agent_answer_cmd)
    else:
        for act, _ in reversed(state.history):
            if isinstance(act, MessageAction) and act.source == 'agent':
                logger.info(act.content)
                agent_answer = act.content
                break

    logger.info(f'Final message: {agent_answer} | Ground truth: {final_ans}')
    test_result = compare_results(check_method, agent_answer, final_ans)

    if config.is_mock:
        histories = ['mock history']
    else:
        histories = [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ]

    # Save the output
    output = {
        'instance_id': inst_id,
        'instance': instance,
        'instruction': instruction,
        'metadata': metadata,
        'history': histories,
        'error': state.error if state and state.error else None,
        'test_result': {
            'agent_answer': agent_answer,
            'final_answer': final_ans,
            'check_method': check_method,
            'result': test_result,
        },
    }

    # Close the sandbox
    sandbox.close()
    return output


def find_subdirectories(directory):
    return [
        name
        for name in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, name))
    ]


def load_datasets_from_local(key: str, _dir: str) -> [dict]:
    _datasets = {}
    if os.path.exists(_dir):
        for filename in os.listdir(_dir):
            if filename.endswith('.json'):  # assuming the datasets are in csv format
                file_path = os.path.join(_dir, filename)
                with open(file_path, 'r') as r:
                    _datasets[filename] = json.load(r)
    return flatten(key, _datasets)


def flatten(key: str, _data: dict) -> [dict]:
    flat_data = []
    for subkey, values in _data.items():
        if isinstance(values, list):
            for i in range(len(values)):
                value = values[i]
                value['instance_id'] = f'{key}_{subkey}_{i}'
                value['task_idx'] = key
                flat_data.append(value)
    return flat_data


if __name__ == '__main__':
    # =============================================
    # load datasets
    # =============================================

    dst_script_dir = config.workspace_base
    snapshot_download(
        repo_id='iFurySt/test', repo_type='dataset', local_dir=dst_script_dir
    )
    data_dir = os.path.join(dst_script_dir, 'os_interaction/data')
    dirs = find_subdirectories(data_dir)
    dirs.sort(key=int)

    agent_bench_tests = []
    for idx in dirs:
        data = load_datasets_from_local(idx, os.path.join(data_dir, idx))
        agent_bench_tests.extend(data)
    logger.info(f'Loaded {len(agent_bench_tests)} tests.')

    # =============================================
    # handle arguments and prepare for evaluation
    # =============================================

    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    logger.info(f'Config for evaluation: {config}')

    # TEST METADATA
    agent_cls = args.agent_cls
    assert (
        agent_cls in AGENT_CLS_TO_FAKE_USER_RESPONSE_FN
    ), f'Unsupported agent class: {agent_cls}'
    model_name = config.llm.model.split('/')[-1]
    max_iterations = args.max_iterations
    eval_note = ''
    if args.eval_note is not None:
        eval_note += '_N_' + args.eval_note
    eval_op_dir = str(
        os.path.join(
            args.eval_output_dir,
            'agent_bench',
            agent_cls,
            model_name + '_maxiter_' + str(max_iterations) + eval_note,
        )
    )

    pathlib.Path(eval_op_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(str(os.path.join(eval_op_dir, 'logs'))).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_op_dir}')

    meta = {
        'agent_class': agent_cls,
        'model_name': model_name,
        'max_iterations': max_iterations,
        'eval_output_dir': eval_op_dir,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        # get the commit id of current repo for reproducibility
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        .decode('utf-8')
        .strip(),
    }
    logger.info(f'Metadata: {meta}')
    with open(os.path.join(eval_op_dir, 'metadata.json'), 'w') as f:
        json.dump(meta, f)

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        agent_bench_tests = agent_bench_tests[:eval_n_limit]
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_op_dir, 'output.jsonl')
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
        f'Evaluation started with Agent {agent_cls}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    # =============================================

    new_agent_bench_tests = []
    for idx, inst in enumerate(agent_bench_tests):
        if inst['instance_id'] in finished_instance_ids:
            logger.info(
                f'Skipping instance {inst['instance_id']} as it is already finished.'
            )
            continue
        new_agent_bench_tests.append(inst)

    agent_bench_tests = new_agent_bench_tests
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(agent_bench_tests)}'
    )

    # =============================================
    # start task
    # =============================================

    pbar = tqdm(total=len(agent_bench_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(fut):
        pbar.update(1)
        output = fut.result()
        pbar.set_description(f'Instance {output["instance_id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        logger.info(
            f'Finished evaluation for instance {output["instance_id"]}: {output["test_result"]["result"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multiprocessing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multiprocessing
            for inst in agent_bench_tests:
                future = executor.submit(
                    process_instance,
                    inst,
                    agent_cls,
                    meta,
                    eval_op_dir,
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
