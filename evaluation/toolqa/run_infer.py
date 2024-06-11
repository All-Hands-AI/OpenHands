import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

from tqdm import tqdm
from utils import download_data, download_tools, encode_question, eval_answer, get_data

from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
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
        'When you think you finished the task, respond with `Finish[answer]` where you include your answer in `[]`\n'
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
    'CodeActAgent': 'When you think you have completed the request, please run the following command: <execute_bash> exit </execute_bash>.\n'
}


def process_instance(task, agent_class, metadata, reset_logger: bool = True):
    # create process-specific workspace dir
    # we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    workspace_mount_path = config.workspace_mount_path
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    eval_output_dir = metadata['eval_output_dir']
    qid = task['qid']
    question = task['question']
    answer = task['answer']
    if reset_logger:
        # Set up logger
        log_file = os.path.join(eval_output_dir, 'logs', f'instance_{qid}.log')
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {qid}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
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

    # Prepare instruction
    instruction = encode_question(question)
    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')
    # logger.info(f'Instruction:\n{instruction}', extra={'msg_type': 'OBSERVATION'})

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
        )
    )
    # ======= Attempt to evaluate the agent's edits =======
    # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    model_answer_raw = ''
    for act, _ in reversed(state.history):
        if isinstance(act, MessageAction) and act.source == 'agent':
            model_answer_raw = act.content
            break
    # attempt to parse model_answer
    correct = eval_answer(str(model_answer_raw), str(answer))
    metrics = state.metrics.get() if state.metrics else None
    logger.info(f'Final message: {model_answer_raw} | Correctness: {correct}')
    # Save the output
    output = {
        'qid': qid,
        'text': model_answer_raw,
        'correct': correct,
        'answer_id': 'None',
        'model_id': metadata['model_name'],
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'metrics': metrics,
        'error': state.error if state and state.error else None,
    }
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        help='Which dataset to evaluate from ToolQA. ToolQA contains 8 datasets, namely agenda, airbnb, coffee, dblp, flight, gsm8k, scirex, yelp. For example, the default is --dataset flight.',
        default='flight',
    )
    parser.add_argument(
        '--hardness',
        type=str,
        help='Which level of difficulty to evaluate from ToolQA. ToolQA contains 2 levels of hardness, namely easy and hard. For example, the default is --hardness easy.',
        default='easy',
    )
    parser.add_argument(
        '--wolfram_alpha_appid',
        type=str,
        help='wolfram alpha appid to use for wolfram alpha related tests',
        default='YOUR_WOLFRAMALPHA_APPID',
    )
    args, _ = parser.parse_known_args()
    if args.directory:
        config.workspace_base = os.path.abspath(args.directory)
        print(f'Setting workspace base to {config.workspace_base}')
    # Check https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/README.md#configure-opendevin-and-your-llm
    # for details of how to set `llm_config`
    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    logger.info(f'Config for evaluation: {config}')
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
        'toolqa',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )
    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_dir, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    dataset = ''
    hardness = ''
    dataset_choices = [
        'agenda',
        'airbnb',
        'coffee',
        'dblp',
        'flight',
        'gsm8k',
        'scirex',
        'yelp',
        'genda',
    ]
    if args.dataset in dataset_choices:
        dataset = args.dataset
    else:
        raise ValueError(
            'Please choose from agenda, airbnb, coffee, dblp, flight, gsm8k, scirex, yelp for dataset.'
        )
    if args.hardness == 'easy':
        hardness = 'easy'
    elif args.hardness == 'hard':
        hardness = 'hard'
    else:
        raise ValueError('Please choose from easy and hard for hardness.')

    logger.info(f'Evaluating ToolQA {dataset} {hardness} test')
    # workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    workspace_mount_path = config.workspace_mount_path
    pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)
    toolqa_test = get_data(dataset, hardness)
    toolqa_data_path = download_data(workspace_mount_path)
    toolqa_tool_path = download_tools(workspace_mount_path, args.wolfram_alpha_appid)

    # TEST METADATA
    metadata = {
        'dataset': dataset,
        'hardness': hardness,
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
    with open(
        os.path.join(eval_output_dir, f'metadata_{dataset}_{hardness}.json'), 'w'
    ) as f:
        json.dump(metadata, f)
    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        toolqa_test = toolqa_test[:eval_n_limit]
        logger.info(
            f'Limiting evaluation to a total of first {eval_n_limit} instances.'
        )
    output_file = os.path.join(
        eval_output_dir, f'output_{model_name}_{dataset}_{hardness}.jsonl'
    )
    logger.info(f'Writing evaluation output to {output_file}')
    finished_task_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                task = json.loads(line)
                finished_task_ids.add(task['qid'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_task_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')
    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )
    # =============================================
    # filter out finished instances
    new_toolqa_test = []
    for task in toolqa_test:
        qid = task['qid']
        if qid in finished_task_ids:
            logger.info(f'Skipping instance {qid} as it is already finished.')
            continue
        new_toolqa_test.append(task)
    finished_task_number = len(finished_task_ids)
    toolqa_test = new_toolqa_test
    logger.info(
        f'Finished instances: {finished_task_number}, Remaining instances: {len(toolqa_test)}'
    )

    # =============================================
    pbar = tqdm(total=len(toolqa_test))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["qid"]}')
        pbar.set_postfix_str(f'Test Result: {output["correct"]}')
        logger.info(
            f'Finished evaluation for instance {output["qid"]}: {output["correct"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()
        finished_task_ids.add(output['qid'])

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')
    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for task in toolqa_test:
                try:
                    future = executor.submit(
                        process_instance,
                        task,
                        agent_class,
                        metadata,
                        reset_logger=bool(num_workers > 1),
                    )
                    future.add_done_callback(update_progress)
                    futures.append(future)
                except Exception:
                    continue
            # Wait for all futures to complete
            for future in futures:
                try:
                    future.result()
                except Exception:
                    continue
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt received. Cleaning up...')
        cleanup()
    output_fp.close()
    total_correct = 0
    output = []
    with open(output_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            output.append(data)
            if data['qid'] in finished_task_ids:
                if str(data['correct']).lower() == 'true':
                    total_correct += 1
    # sort all output by question_id
    output = sorted(output, key=lambda x: x['qid'])
    with open(output_file, 'w') as f:
        for dat in output:
            f.write(json.dumps(dat) + '\n')
            f.flush()
    logger.info(
        f'Evaluation finished for {dataset}-{hardness}. Total: {len(toolqa_test)+finished_task_number}; Correct: {total_correct}; Accuracy: {total_correct / (len(toolqa_test)+finished_task_number)}'
    )
