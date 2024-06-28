import asyncio
import functools
import json
import logging
import multiprocessing as mp
import os
import pathlib
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Dict

import tasks
from config_variables import TASK_INFO_MAP
from datasets import load_dataset
from datatypes import TaskState
from env import SimplifiedEnv
from prompts import ToolPromptTemplate
from tasks import Task
from tqdm import tqdm

from evaluation.swe_bench.swe_env_box import DockerSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.serialization.event import event_to_dict


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State, task: Task, task_config: Dict[str, int]):
    logger.info(f'Gold reference: {task.reference}')
    logger.info(f'Task config: {task_config}')

    env = SimplifiedEnv(
        agent_state=state,
        task=task,
        task_config=task_config,
    )
    last_action, _ = state.history[-1]
    result_state: TaskState = env.step(last_action.message)

    state.task_state = result_state

    if not result_state.latest_output:
        # Task is finished
        msg = '/exit'
    else:
        msg = result_state.latest_output['content']

    logger.info('User response:' + msg)
    return msg


def monologue_user_response(state: State) -> str:
    raise NotImplementedError('MonologueAgent should never ask for user responses.')


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'MonologueAgent': monologue_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': '\nIMPORTANT: When your answer is confirmed by the user to be correct, you can exit using the following command: <execute_bash> exit </execute_bash>.\n'
}


def process_instance(
    instance: Task,
    agent_class,
    metadata,
    skip_workspace_mount,
    eval_output_dir,
    reset_logger: bool = True,
):
    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    # create process-specific workspace dir
    # if `not skip_workspace_mount` - we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    if not skip_workspace_mount:
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            eval_output_dir, 'logs', f'instance_{instance.task_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance.task_id}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
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

    sandbox = DockerSSHBox()

    requirements_host_src = 'evaluation/mint/requirements.txt'
    requirements_sandbox_dest = '/opendevin/plugins/mint/requirements.txt'
    sandbox.copy_to(
        host_src=requirements_host_src,
        sandbox_dest=requirements_sandbox_dest,
        recursive=False,
    )
    logger.info(
        f'Copied files from [{requirements_host_src}] to [{requirements_sandbox_dest}] inside sandbox.'
    )
    exit_code, output = sandbox.execute(f'pip install -r {requirements_sandbox_dest}')

    # Prepare instruction
    instruction = ToolPromptTemplate(use_tool=True)(
        max_total_steps=metadata['max_iterations'],
        max_propose_solution=metadata['max_propose_solution'],
        in_context_example=instance.in_context_example(
            use_tool=True, with_feedback=False
        ),
        task_prompt='Task:\n' + instance.prompt,
    )
    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you or provide the concise RESULT inside <solution> tag AND NEVER ASK FOR HUMAN HELP.\n'

    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    fake_user_response_fn = functools.partial(
        AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
        task=instance,
        task_config={
            'max_iterations': metadata['max_iterations'],
            'max_propose_solution': metadata['max_propose_solution'],
        },
    )

    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=fake_user_response_fn,
            sandbox=sandbox,
        )
    )

    if state is None:
        raise ValueError('State should not be None.')

    task_state = None
    if hasattr(state, 'task_state'):
        task_state = state.task_state
        logger.info('Task state: ' + str(task_state.to_dict()))

    metrics = state.metrics.get() if state.metrics else None

    # Save the output
    output = {
        'id': instance.task_id,
        'instance': instance.to_dict(),
        'instruction': instruction,
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'metrics': metrics,
        'error': state.error if state and state.error else None,
        'test_result': task_state.success if task_state else False,
    }

    # Close the sandbox
    sandbox.close()

    return output


if __name__ == '__main__':
    parser = get_parser()

    parser.add_argument(
        '--subset',
        default='math',
        choices=['math', 'gsm8k', 'mmlu', 'theoremqa', 'mbpp', 'humaneval'],
        type=str,
        help='subset of the dataset to be used',
    )
    parser.add_argument(
        '--max-propose-solution',
        default=2,
        type=int,
        help='maximum number of times the agent can propose a solution',
    )

    args, _ = parser.parse_known_args()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    mint_dataset = load_dataset(
        'ryanhoangt/xingyaoww-mint-bench', name=args.subset, split='test'
    )
    logger.info(f'Evaluating MINT - {args.subset} subset')

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
        'mint',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
        args.subset,
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
        'max_propose_solution': args.max_propose_solution,
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
        mint_dataset = mint_dataset.select(range(eval_n_limit))
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_instance_ids.add(data['id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_instance_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}, max propose solution {args.max_propose_solution}.'
    )

    # =============================================
    # filter out finished instances
    task_class: Task = getattr(tasks, TASK_INFO_MAP[args.subset]['class'])
    new_mint_tests: list[Task] = []

    for instance in mint_dataset:
        if instance['id'] in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance["id"]} as it is already finished.'
            )
            continue
        # convert to Task object
        instance = task_class(**instance)
        new_mint_tests.append(instance)

    mint_dataset = new_mint_tests
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(mint_dataset)}'
    )
    # =============================================

    pbar = tqdm(total=len(mint_dataset))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        # logger.info('Output: ', output)
        # pbar.set_description(f'Instance {output["instance_id"]}')
        # pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        # logger.info(
        #     f'Finished evaluation for instance {output["instance_id"]}: {output["test_result"]["result"]}'
        # )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    # This is SWE-Bench specific - CodeActAgent doesn't require mounted workspace to work
    skip_workspace_mount = agent_class == 'CodeActAgent'
    logger.info(f'Skipping workspace mount: {skip_workspace_mount}')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for instance in mint_dataset:
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
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
    logger.info('Evaluation finished.')
