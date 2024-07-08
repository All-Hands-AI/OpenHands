import asyncio
import logging
import os
import re
import shutil

import docker
import pandas as pd
from datasets import load_dataset

from evaluation.agent_bench.helper import (
    FAKE_RESPONSES,
    INST_SUFFIXES,
    compare_results,
    create_sh_file,
)
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
from opendevin.events.action import CmdRunAction, MessageAction
from opendevin.llm.llm import LLM
from opendevin.runtime.docker.ssh_box import DockerSSHBox


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    # Create the agent
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(llm_config=metadata.llm_config))

    inst_id = instance.instance_id
    question = instance.description
    # create a directory for the instance's workspace
    instance_workspace = str(os.path.join(config.workspace_base, inst_id))
    container_inst_workspace = str(
        os.path.join(config.workspace_mount_path_in_sandbox, inst_id)
    )
    if os.path.exists(instance_workspace):
        shutil.rmtree(instance_workspace)
    os.makedirs(instance_workspace, exist_ok=True)

    # Set up the logger properly, so you can run multiprocessing to parallel the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            metadata.eval_output_dir, 'logs', f'instance_{inst_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {inst_id}.\nHint: run "tail -f {log_file}" to see live logs in a separate shell'
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
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        'Please encapsulate your final answer (answer ONLY) within <solution> and </solution>.\n'
        'For example: The answer to the question is <solution> 42 </solution>.\n'
        '# Problem \n'
        f'{question}\n\n'
    )
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided '
        'to you AND NEVER ASK FOR HUMAN HELP.\n'
    )
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += INST_SUFFIXES[agent.__class__.__name__]

    # =============================================
    # create sandbox and run the agent
    # =============================================

    sandbox = DockerSSHBox()
    sandbox.execute(f'cd {inst_id}')

    init_cmd = instance.init
    if init_cmd is not None:
        scpt_name = f'{instance.instance_id}_init.sh'
        scpt_path = os.path.join(container_inst_workspace, scpt_name)
        host_scpt_path = os.path.join(instance_workspace, scpt_name)
        create_sh_file(host_scpt_path, init_cmd)
        logger.info(f'Running init script: {scpt_path}')
        _, init_res = sandbox.execute(scpt_path)
        logger.info(f'Init script result: {init_res}')

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State | None = asyncio.run(
        run_agent_controller(
            agent,
            instruction,
            max_iterations=metadata.max_iterations,
            fake_user_response_fn=FAKE_RESPONSES[agent.__class__.__name__],
            sandbox=sandbox,
            sid=inst_id,
        )
    )

    if state is None:
        raise ValueError('State should not be None.')

    # get the ground truth
    # OSBenchSSHBox.get_ground_truth(instance, state)

    # =============================================
    # result evaluation
    # =============================================

    agent_answer = ''
    get_agent_result_cmd = instance.get_agent_result
    if get_agent_result_cmd is not None:
        scpt_name = f'{instance.instance_id}_get_agent_result.sh'
        scpt_path = os.path.join(container_inst_workspace, scpt_name)
        host_scpt_path = os.path.join(instance_workspace, scpt_name)
        create_sh_file(host_scpt_path, get_agent_result_cmd)
        logger.info(f'Running get agent result cmd: {scpt_path}')
        _, agent_answer = sandbox.execute(scpt_path)
    else:
        logger.info('Retrieving agent answer from history.')
        raw_ans = ''

        # retrieve the last agent message or thought
        for event in state.history.get_events(reverse=True):
            if isinstance(event, MessageAction) and event.source == 'agent':
                raw_ans = event.content
            elif isinstance(event, CmdRunAction) and event.source == 'agent':
                raw_ans = event.thought

        # parse the answer for a solution tag
        agent_answer = re.findall(r'<solution>(.*?)</solution>', raw_ans)
        if len(agent_answer) == 0:
            logger.warning(f'Failed to parse model answer: {raw_ans}')
            agent_answer = raw_ans
        else:
            agent_answer = agent_answer[0]

    final_ans = ''
    if instance.ground_truth is not None:
        final_ans = instance.ground_truth
    else:
        get_ground_truth_cmd = instance.get_ground_truth
        if get_ground_truth_cmd is not None:
            scpt_name = f'{instance.instance_id}_get_ground_truth.sh'
            scpt_path = os.path.join(container_inst_workspace, scpt_name)
            host_scpt_path = os.path.join(instance_workspace, scpt_name)
            create_sh_file(host_scpt_path, get_ground_truth_cmd)
            logger.info(f'Running get ground truth cmd: {scpt_path}')
            sandbox.execute(f'cd {container_inst_workspace}')
            _, final_ans = sandbox.execute(scpt_path)

    comparison_method = instance.comparison_method
    logger.info(
        f'Final message: {agent_answer} | Ground truth: {final_ans} | Comparison method: {comparison_method}'
    )
    test_result = compare_results(comparison_method, agent_answer, final_ans)

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = state.history.compatibility_for_eval_history_pairs()

    metrics = state.metrics.get() if state.metrics else None

    # Save the output
    output = {
        'instance_id': inst_id,
        'instance': instance.to_dict(),
        'instruction': instruction,
        'metadata': metadata.model_dump(),
        'history': histories,
        'metrics': metrics,
        'error': state.last_error if state and state.last_error else None,
        'test_result': {
            'agent_answer': agent_answer,
            'final_answer': final_ans,
            'check_method': comparison_method,
            'result': test_result,
        },
    }

    # clean up
    if os.path.exists(instance_workspace):
        shutil.rmtree(instance_workspace)
    # Close the sandbox
    try:
        sandbox.close()
    except docker.errors.NotFound as e:
        logger.error(f'Failed to close sandbox: {e}')
    return output


if __name__ == '__main__':
    id_column = 'instance_id'
    args = parse_arguments()
    dataset = load_dataset('iFurySt/AgentBench')
    agent_bench_tests = dataset['osbench'].to_pandas()

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
