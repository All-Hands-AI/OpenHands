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
from utils import encode_question, get_data

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
        #'Please continue working on the task on whatever approach you think is suitable.\n'
        'Please run the following command: <execute_bash> exit </execute_bash>.\n'
        #'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK.\n'
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


def process_instance(
    question_id, question, agent_class, metadata, reset_logger: bool = True
):
    # create process-specific workspace dir
    # we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    old_workspace_mount_path = config.workspace_mount_path
    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)
        config.workspace_mount_path = workspace_mount_path

        # Setup the logger properly, so you can run multi-processing to parallize the evaluation
        eval_output_dir = metadata['eval_output_dir']
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                eval_output_dir, 'logs', f'instance_{question_id}.log'
            )
            # Remove all existing handlers from logger
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # add back the console handler to print ONE line
            logger.addHandler(get_console_handler())
            logger.info(
                f'Starting evaluation for instance {question_id}.\nLOG:   tail -f {log_file}'
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
        instruction = encode_question(question, metadata['hub'])
        instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        # NOTE: You can actually set slightly different instruction for different agents
        instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')
        # logger.info(f'Instruction:\n{instruction}', extra={'msg_type': 'OBSERVATION'})

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State = asyncio.run(
            main(
                instruction,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                    agent_class
                ),
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
        _, _, ast_eval = get_data(metadata['hub'])
        correct, hallucination = ast_eval(question_id, model_answer_raw)
        metrics = state.metrics.get() if state.metrics else None
        logger.info(
            f'Final message: {model_answer_raw} | Correctness: {correct} | Hallucination: {hallucination}'
        )
        # Save the output
        output = {
            'question_id': question_id,
            'text': model_answer_raw,
            'correct': correct,
            'hallucination': hallucination,
            'answer_id': 'None',
            'model_id': metadata['model_name'],
            'metadata': metadata,
            'history': [
                (event_to_dict(action), event_to_dict(obs))
                for action, obs in state.history
            ],
            'metrics': metrics,
            'error': state.error if state and state.error else None,
        }
    except Exception:
        logger.error('Process instance failed')
        raise
    finally:
        config.workspace_mount_path = old_workspace_mount_path
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--hubs',
        type=str,
        help='Which hubs to evaluate from APIBench. APIBench contains 3 hubs, namely huggingface, torch, and tensorflow. You could choose one or more from hf, torch, or tf, separated by commas. For example, the default is --hub hf,torch,tf.',
        default='hf,torch,tf',
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
        'gorilla',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )
    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_dir, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    hubs = []
    if 'hf' in args.hubs:
        hubs.append('hf')
    if 'torch' in args.hubs or 'th' in args.hubs:
        hubs.append('torch')
    if 'tf' in args.hubs:
        hubs.append('tf')
    if hubs == []:
        raise ValueError('Please choose at least one from hf, torch, and tf for hubs.')

    for hub in hubs:
        logger.info(f'Evaluating APIBench {hub} test')
        questions, question_ids, ast_eval = get_data(hub)

        # TEST METADATA
        metadata = {
            'hub': hub,
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
        with open(os.path.join(eval_output_dir, f'metadata_{hub}.json'), 'w') as f:
            json.dump(metadata, f)

        # LIMIT EVALUATION
        eval_n_limit = args.eval_n_limit
        if eval_n_limit:
            questions = questions[: (eval_n_limit // len(hubs))]
            question_ids = question_ids[: (eval_n_limit // len(hubs))]
            logger.info(
                f'Limiting evaluation to a total of first {eval_n_limit} instances -> first {eval_n_limit//len(hubs)} instances per hub.'
            )
        output_file = os.path.join(eval_output_dir, f'output_{model_name}_{hub}.jsonl')
        logger.info(f'Writing evaluation output to {output_file}')
        finished_task_ids = set()
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    for i in range(len(question_ids)):
                        if question_ids[i] == int(data['question_id']):
                            finished_task_ids.add(data['question_id'])
            logger.warning(
                f'Output file {output_file} already exists. Loaded {len(finished_task_ids)} finished instances.'
            )
        output_fp = open(output_file, 'a')
        logger.info(
            f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
        )
        # =============================================
        # filter out finished instances
        new_questions = []
        new_question_ids = []
        for i in range(len(question_ids)):
            if question_ids[i] in finished_task_ids:
                logger.info(
                    f'Skipping instance {question_ids[i]} as it is already finished.'
                )
                continue
            new_questions.append(questions[i])
            new_question_ids.append(question_ids[i])

        finished_task_number = len(finished_task_ids)
        questions = new_questions
        question_ids = new_question_ids
        logger.info(
            f'Finished instances: {finished_task_number}, Remaining instances: {len(question_ids)}'
        )
        # =============================================
        pbar = tqdm(total=len(question_ids))

        # This function tracks the progress AND write the output to a JSONL file
        def update_progress(future, pbar, output_fp, finished_task_ids):
            pbar.update(1)
            output = future.result()
            pbar.set_description(f'Instance {output["question_id"]}')
            pbar.set_postfix_str(f'Test Result: {output["correct"]}')
            logger.info(
                f'Finished evaluation for instance {output["question_id"]}: {output["correct"]}'
            )
            output_fp.write(json.dumps(output) + '\n')
            output_fp.flush()
            finished_task_ids.add(output['question_id'])

        # This sets the multi-processing
        num_workers = args.eval_num_workers
        logger.info(f'Using {num_workers} workers for evaluation.')
        try:
            with ProcessPoolExecutor(num_workers) as executor:
                futures = []
                # This is how we perform multi-processing
                for i in range(len(question_ids)):
                    try:
                        question_id = question_ids[i]
                        question = questions[i]
                        future = executor.submit(
                            process_instance,
                            question_id,
                            question,
                            agent_class,
                            metadata,
                            reset_logger=bool(num_workers > 1),
                        )
                        future.add_done_callback(
                            update_progress, pbar, output_fp, finished_task_ids
                        )
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
        total_hallucination = 0
        output = []
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                output.append(data)
                if int(data['question_id']) in finished_task_ids:
                    if str(data['correct']).lower() == 'true':
                        total_correct += 1
                    if str(data['hallucination']).lower() == 'true':
                        total_hallucination += 1
        # sort all output by question_id
        output = sorted(output, key=lambda x: x['question_id'])
        with open(output_file, 'w') as f:
            for dat in output:
                f.write(json.dumps(dat) + '\n')
                f.flush()

        logger.info(
            f'Evaluation finished for {hub}. Total: {len(question_ids)+finished_task_number}; Correct: {total_correct}; Hallucination: {total_hallucination}. Accuracy: {total_correct / (len(question_ids)+finished_task_number)}'
        )
