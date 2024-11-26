# FILE: run_infer.py

import asyncio
import os
import shutil
import tempfile
from functools import partial

import pandas as pd
from datasets import load_dataset

from evaluation.benchmarks.visualcodebench.eval import capture_screenshot
from evaluation.benchmarks.visualcodebench.prepare import (
    REPO_DOWNLOAD_DIR,
    download_repository,
    pil_image_to_base64,
    prepare_visualcodebench,
)
from evaluation.utils.shared import (
    EvalMetadata,
    assert_and_raise,
    codeact_user_response,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
    SandboxConfig,
    get_llm_config_arg,
)
from openhands.core.config.utils import parse_arguments
from openhands.core.logger import openhands_logger as logger  # Import OpenHands logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action.commands import CmdRunAction
from openhands.events.action.message import MessageAction
from openhands.events.observation.commands import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

# Define workspace and output directories
WORKSPACE_DIR = './workspace'

FAKE_RESPONSES = {
    'CodeActAgent': partial(codeact_user_response, encapsulate_solution=True),
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='eventstream',
        max_iterations=metadata.max_iterations,
        sandbox=SandboxConfig(
            base_container_image='python:3.12-bookworm',
            enable_auto_lint=True,
            use_host_network=False,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    return config


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info('-' * 30)
    logger.info('BEGIN Runtime Initialization Fn')
    logger.info('-' * 30)
    workspace_dir_name = instance['instance_id']
    obs: CmdOutputObservation

    action = CmdRunAction(command='mkdir -p /workspace/{workspace_dir_name}')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to create /workspace/{workspace_dir_name}: {str(obs)}',
    )

    file_path = REPO_DOWNLOAD_DIR + f'data/{workspace_dir_name}/prev/index.html'
    runtime.copy_to(file_path, f'/workspace/{workspace_dir_name}')
    logger.info(f'Copied code file for instance {workspace_dir_name}')

    action = CmdRunAction(command=f'cd /workspace/{workspace_dir_name}')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert_and_raise(
        obs.exit_code == 0,
        f'Failed to cd to /workspace/{workspace_dir_name}: {str(obs)}',
    )

    logger.info('-' * 30)
    logger.info('END Runtime Initialization Fn')
    logger.info('-' * 30)


def complete_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required, but it is used to get the workspace_dir_name
) -> str:
    # TODO: extract edited HTML file from agent workspace
    # temp_zip = runtime.copy_from(f'/workspace/{instance.instance_id}')
    # file_name = f'/workspace/{instance.instance_id}/index.html'
    # with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
    #     if file_name in zip_ref.namelist():
    #         with zip_ref.open(file_name) as file:
    #             file_content = file.read().decode('utf-8')  # Decode bytes to string
    #     else:
    #         raise FileNotFoundError(f"'{file_name}' not found in the ZIP archive.")

    with tempfile.TemporaryDirectory() as tmpdir:
        src_folder = REPO_DOWNLOAD_DIR + f'data/{instance.instance_id}/post/'
        shutil.copytree(src_folder, tmpdir, dirs_exist_ok=True)

        image = capture_screenshot(tmpdir)
        if image is not None:
            shutil.copy(os.path.join(tmpdir, 'final_screenshot.png'), REPO_DOWNLOAD_DIR)


def process_instance(
    instance: pd.Series, metadata: EvalMetadata, reset_logger: bool = True
):
    config = get_config(metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    # =============================================
    # build instruction
    # =============================================

    # Prepare instruction
    instruction = (
        f"Modify the HTML/CSS according to the following instruction:\n\n"
        f"{instance['changes']}\n\n"
    )
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided '
        'to you AND NEVER ASK FOR HUMAN HELP.\n'
    )

    # =============================================
    # create sandbox and run the agent
    # =============================================

    runtime: Runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)

    try:
        initialize_runtime(runtime, instance=instance)

        image_urls = pil_image_to_base64(instance['prev_image'])

        action = MessageAction(content=instruction, image_urls=image_urls)
        state: State | None = asyncio.run(
            run_controller(
                config=config,
                initial_user_action=action,
                runtime=runtime,
                fake_user_response_fn=FAKE_RESPONSES[metadata.agent_class],
            )
        )
        if state is None:
            raise ValueError('State should not be None.')

        # =============================================
        # result evaluation
        # =============================================

        return_val = complete_runtime(runtime, instance)
        logger.info(f'Return value {return_val}')
    finally:
        runtime.close()

    # TODO: return EVAL output


def main():
    """Main function to run the evaluation."""
    # args = parse_args()
    args = parse_arguments()

    logger.info(f"\n{'='*80}\nStarting VisualCodeBench Evaluation\n{'='*80}")
    logger.info(f'Agent: {args.agent_cls}')
    logger.info(f'Model: {args.llm_config}')
    logger.info(f'Max iterations: {args.max_iterations}')
    logger.info(f'Eval limit: {args.eval_n_limit}')
    logger.info(f'Num workers: {args.eval_num_workers}\n')
    logger.info(f'Eval output: {args.eval_output_dir}\n')

    # Step 1: Download the entire repository once
    logger.info('Downloading repository...')
    download_repository()

    # Step 2: Load Dataset
    logger.info('Loading dataset...')
    dataset = load_dataset(REPO_DOWNLOAD_DIR)

    # Step 3: Prepare dataset
    llm_config = get_llm_config_arg(args.llm_config)
    if llm_config is None:
        logger.error(f'Could not find LLM config: {args.llm_config}')
        raise ValueError(f'Could not find LLM config: {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'VisualCodeBench',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        'evaluation/output/',
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    dataset = prepare_visualcodebench(dataset)
    instances = prepare_dataset(dataset, output_file, eval_n_limit=args.eval_n_limit)

    # Step 4: Run eval
    run_evaluation(
        instances, metadata, output_file, args.eval_num_workers, process_instance
    )


if __name__ == '__main__':
    main()
