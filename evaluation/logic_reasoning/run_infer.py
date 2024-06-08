import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import shutil
import time
from concurrent.futures import ProcessPoolExecutor

from datasets import load_dataset
from tqdm import tqdm

from evaluation.swe_bench.swe_env_box import DockerSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
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
        'If you think you have solved the task, please run the following command: <execute_bash> exit </execute_bash>.\n'
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
    'CodeActAgent': 'When you think you have solved the question, please first send your answer to user through message and then exit.\n'
}


def get_choice(answer_str):
    choices = [
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'A)',
        'B)',
        'C)',
        'D)',
        'E)',
        'F)',
        'G)',
        'H)',
        'A.',
        'B.',
        'C.',
        'D.',
        'E.',
        'F.',
        'G.',
        'H.',
    ]
    for c in choices:
        if answer_str.startswith(c):
            return c.replace(')', '')

    if answer_str.startswith(':'):
        return answer_str.replace(':', '').replace('.', '').strip()
    return None


def get_test_result(
    model_answer: str,
    ground_truth: str,
) -> bool:
    gold_answer = ground_truth.replace('(', '').replace(')', '').strip()
    answer_str = model_answer if model_answer is not None else ''
    prediction = get_choice(answer_str)

    indicators = [
        'the correct option is',
        'the correct answer is',
        'The correct answer is',
        'The correct option is',
        'Thus, the answer is',
    ]
    if prediction is None:
        for indicator in indicators:
            if answer_str.find(indicator) >= 0:
                answer_str = answer_str.split(indicator)[1].strip()
                prediction = get_choice(answer_str)
                break

    isTrue = prediction == gold_answer
    test_result = {'result': isTrue}
    return test_result


def process_instance(
    instance,
    agent_class,
    # metadata,
    dataset_name,
    skip_workspace_mount,
    eval_output_dir,
    reset_logger: bool = True,
):
    old_workspace_mount_path = config.workspace_mount_path
    old_workspace_base = config.workspace_base

    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        # create process-specific workspace dir
        # if `not skip_workspace_mount` - we will create a workspace directory for EACH process
        # so that different agent don't interfere with each other.
        if not skip_workspace_mount:
            workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
            pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

        # reset workspace to config
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                eval_output_dir, 'logs', f'instance_{instance["id"]}.log'
            )
            # Remove all existing handlers from logger
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # add back the console handler to print ONE line
            logger.addHandler(get_console_handler())
            logger.info(
                f'Starting evaluation for instance {instance["id"]}.\nLOG:   tail -f {log_file}'
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

        # sandbox = DockerSSHBox()
        logic_inference_path = os.path.join(workspace_mount_path, 'logic_inference.py')
        if not os.path.exists(logic_inference_path):
            shutil.copyfile(
                './evaluation/logic_reasoning/logic_inference.py', logic_inference_path
            )
        logger.info(f'logic_inference.py copied to {workspace_mount_path}')

        cache_dir = os.path.join(workspace_mount_path, '.cache_program')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # Prepare instruction

        with open('./evaluation/logic_reasoning/instruction.txt', 'r') as f:
            instruction = f.read()

        instance_logic_programs = instance['raw_logic_programs'][0].strip()
        instruction = instruction.replace('[[dataset_name]]', dataset_name)
        instruction = instruction.replace('[[logic_programs]]', instance_logic_programs)
        instruction = instruction.replace(
            '[[logic_inference_path.py]]', logic_inference_path
        )

        # NOTE: You can actually set slightly different instruction for different agents
        instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

        sandbox = DockerSSHBox()
        exit_code, command_output = sandbox.execute('pip install scitools-pyke')

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State = asyncio.run(
            main(
                instruction,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                    agent_class
                ),
                sandbox=sandbox,
            )
        )
        # ======= Attempt to evaluate the agent's edits =======
        # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
        # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

        if state is None:
            raise ValueError('State should not be None.')

        final_message = ''
        messages = []
        for action, obs in reversed(state.history):
            # if isinstance(act, MessageAction):
            messages.append(obs.content)
            # print("obs.content:", obs.content)
            if str(obs.content) in ["'A'", "'B'", "'C'"]:
                final_message = obs.content
                break

        final_message = final_message.strip("'")
        logger.info(
            f'Predicted answer: {final_message}, Ground truth: {instance["answer"]}'
        )

        test_result = get_test_result(
            model_answer=final_message, ground_truth=instance['answer']
        )
        metrics = state.metrics.get() if state.metrics else None

        # Save the output
        output = {
            'id': instance['id'],
            'instance': instance,
            'instruction': instruction,
            # 'metadata': metadata,
            'history': [
                (event_to_dict(action), event_to_dict(obs))
                for action, obs in state.history
            ],
            'metrics': metrics,
            'final_message': final_message,
            'messages': messages,
            'error': state.error if state and state.error else None,
            'test_result': test_result,
        }
    except Exception:
        logger.error('Process instance failed')
        raise
    finally:
        config.workspace_mount_path = old_workspace_mount_path
        config.workspace_base = old_workspace_base

    # Close the sandbox
    sandbox.close()

    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        help='the logic reasoning dataset to evaluate on {ProntoQA, ProofWriter}',
        default='ProntoQA',
    )
    parser.add_argument(
        '--data_split',
        type=str,
        help='data split to evaluate on {validation}',  # right now we only support validation split
        default='validation',
    )

    args, _ = parser.parse_known_args()
    if args.directory:
        config.workspace_base = os.path.abspath(args.directory)
        print(f'Setting workspace base to {config.workspace_base}')
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo

    dataset_name = args.dataset
    data_split = args.data_split
    dataset = load_dataset(f'renma/{dataset_name}')
    logic_reasoning_tests = dataset[data_split]
    logger.info(f'Evaluating logic reasoning dataset {dataset_name} {data_split} split')

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
        'logic_reasoning',
        agent_class,
        dataset_name,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )

    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_dir, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        logic_reasoning_tests = logic_reasoning_tests.select(list(range(eval_n_limit)))
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    start_time = time.strftime('%Y-%m-%d %H:%M:%S')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_task_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_task_ids.add(data['id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_task_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_logic_reasoning_tests = []
    for instance in logic_reasoning_tests:
        if instance['id'] in finished_task_ids:
            logger.info(
                f'Skipping instance {instance["id"]} as it is already finished.'
            )
            continue
        new_logic_reasoning_tests.append(instance)

    logic_reasoning_tests = new_logic_reasoning_tests
    logger.info(
        f'Finished instances: {len(finished_task_ids)}, Remaining instances: {len(logic_reasoning_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(logic_reasoning_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        logger.info(
            f'Finished evaluation for instance {output["id"]}: {output["test_result"]["result"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        # json.dump(output, output_fp, indent=4)
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    # num_workers = 1
    logger.info(f'Using {num_workers} workers for evaluation.')

    # This is SWE-Bench specific - CodeActAgent don't requires mounted workspace to work
    skip_workspace_mount = False
    logger.info(f'Skipping workspace mount: {skip_workspace_mount}')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for instance in logic_reasoning_tests:
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    dataset_name,
                    skip_workspace_mount,
                    eval_output_dir,
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

    with open(output_file, 'r') as f:
        test_result = [(json.loads(line))['test_result']['result'] for line in f]

    metadata = {
        'Dataset': dataset_name,
        'Data split': data_split,
        'Number of Samples': len(test_result),
        'Agent class': agent_class,
        'Model name': model_name,
        'Start_time': start_time,
        'End_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'Final Accuracy': f'{sum(test_result)/len(test_result):.2f}',
    }

    with open(os.path.join(eval_output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)

    logger.info(f'Metadata: {json.dumps(metadata, indent=4)}')
    logger.info(
        f'Evaluation finished. Metadata saved to {eval_output_dir}/metadata.json'
    )
