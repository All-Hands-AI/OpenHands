import asyncio
import logging
import os
import pathlib
import shutil

import pandas as pd
from datasets import load_dataset

from evaluation.swe_bench.swe_env_box import DockerSSHBox
from evaluation.utils.shared import (
    EvalMetadata,
    codeact_user_response,
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import get_llm_config_arg, get_parser, load_app_config
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM

config = load_app_config()

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
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
) -> dict[str, bool]:
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
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(config=metadata.llm_config))
    old_workspace_mount_path = config.workspace_mount_path
    old_workspace_base = config.workspace_base

    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        # create process-specific workspace dir
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

        # reset workspace to config
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                metadata.eval_output_dir, 'logs', f'instance_{instance["id"]}.log'
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
        instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]

        # use a session id for concurrent evaluation
        sid = instance['id'] + '_' + str(os.getpid())
        sandbox = DockerSSHBox(
            config=config.sandbox,
            persist_sandbox=False,
            workspace_mount_path=config.workspace_mount_path,
            sandbox_workspace_dir=config.workspace_mount_path_in_sandbox,
            cache_dir=config.cache_dir,
            run_as_devin=config.run_as_devin,
            sid=sid,
        )
        exit_code, command_output = sandbox.execute('pip install scitools-pyke')

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State | None = asyncio.run(
            run_agent_controller(
                agent,
                instruction,
                max_iterations=metadata.max_iterations,
                max_budget_per_task=config.max_budget_per_task,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                    agent.__class__.__name__
                ),
                sandbox=sandbox,
                sid=sid,
            )
        )
        # ======= Attempt to evaluate the agent's edits =======
        # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
        # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

        if state is None:
            raise ValueError('State should not be None.')

        final_message = ''
        messages = []
        for event in state.history.get_events(reverse=True):
            # will this be a MessageAction?
            # TODO we can filter for types of events if we know what to expect
            messages.append(event.content)
            if str(event.content) in ["'A'", "'B'", "'C'"]:
                final_message = event.content
                break

        final_message = final_message.strip("'")
        logger.info(
            f'Predicted answer: {final_message}, Ground truth: {instance["answer"]}'
        )

        test_result = get_test_result(
            model_answer=final_message, ground_truth=instance['answer']
        )
        metrics = state.metrics.get() if state.metrics else None

        # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
        # for compatibility with the existing output format, we can remake the pairs here
        # remove when it becomes unnecessary
        histories = state.history.compatibility_for_eval_history_pairs()

        # Save the output
        output = {
            'id': instance['id'],
            'instance': instance,
            'instruction': instruction,
            # 'metadata': metadata.model_dump(),
            'history': histories,
            'metrics': metrics,
            'final_message': final_message,
            'messages': messages,
            'error': state.last_error if state and state.last_error else None,
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

    dataset_name = args.dataset
    data_split = args.data_split
    dataset = load_dataset(f'renma/{dataset_name}')
    logic_reasoning_tests = dataset[data_split]

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
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
