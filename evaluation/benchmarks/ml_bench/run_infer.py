"""Implements evaluation of agents on ML-Bench, a benchmark for assessing the effectiveness of
Large Language Models (LLMs) in leveraging existing functions in open-source libraries for
machine learning tasks. The benchmark is introduced in the paper "ML-Bench: Evaluating Large
Language Models for Code Generation in Repository-Level Machine Learning Tasks"
(https://arxiv.org/abs/2311.09835).

Please see https://ghcr.io/super-dainiu/ml_bench and https://huggingface.co/datasets/super-dainiu/ml-bench
for more details on the dataset and docker image used in this evaluation script.

TODOs:
- Support additional evaluation settings, such as providing raw README content or using a
  retriever to extract relevant segments.
- Clean up the code and docker image used for evaluation.
"""

import asyncio
import os
from typing import Any

import pandas as pd
from datasets import load_dataset

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    codeact_user_response,
    compatibility_for_eval_history_pairs,
    get_default_sandbox_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
    get_llm_config_arg,
    get_parser,
    load_app_config,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

config = load_app_config()

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have completed the task, please finish the interaction using the "finish" tool.\n'
}

ID2CONDA = {
    1: 'dgl_DS',
    2: 'bert_DS',
    3: 'lavis_DS',
    4: 'if_DS',
    5: 'V2V_DS',
    6: 'esm_DS',
    7: 'OP_DS',
    8: 'TSL_DS',
    9: 'EAP_DS',
    10: 'PG_DS',
    11: 'PIM_DS',
    12: 'AD2_DS',
    13: 'L3_DS',
    14: 'MZ2_DS',
    15: 'GSA2_DS',
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'public.ecr.aws/i5g0m1f6/ml-bench'
    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=sandbox_config,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.enable_prompt_extensions = False
    return config


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Initialization Fn {'-' * 50}")
    obs: CmdOutputObservation

    # Set instance id
    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    # Set up the task environment
    action = CmdRunAction(command=f'conda activate {ID2CONDA[instance["github_id"]]}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    repo_url = instance['github']
    repo_name = repo_url.split('/')[-1]
    action = CmdRunAction(command=f'git clone {repo_url} /workspace/{repo_name}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command=f'chmod -R 777 /workspace/{repo_name}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    # Navigate to the task's code path
    task_path = os.path.join('/workspace', repo_name, instance['path'][2:])
    action = CmdRunAction(command=f'cd {task_path}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    logger.info(f"{'-' * 50} END Runtime Initialization Fn {'-' * 50}")


def complete_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required, but it is used to get the workspace_dir_name
) -> dict[str, Any]:
    """Complete the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    If you need to do something in the sandbox to get the correctness metric after
    the agent has run, modify this function.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Completion Fn {'-' * 50}")
    obs: CmdOutputObservation

    repo_url = instance['github']
    repo_name = repo_url.split('/')[-1]
    task_path = os.path.join('/workspace', repo_name, instance['path'][2:])

    # Evaluate the agent's script
    eval_script = os.path.join(task_path, 'run.sh')
    logger.info(f'Running evaluation script: {eval_script}')

    action = CmdRunAction(command=f'cat {eval_script}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    if obs.exit_code == 0:
        eval_script_content = obs.content
    else:
        logger.error(f'Error reading evaluation script: {obs.content}')
        eval_script_content = ''

    action = CmdRunAction(
        command=f'timeout 120s conda run -n {ID2CONDA[instance["github_id"]]} bash {eval_script}',
        timeout=600,
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    if obs.exit_code == 0:
        eval_output = obs.content
    else:
        logger.error(f'Error running evaluation script: {obs.content}')
        eval_output = ''

    outputs = {
        'eval_script_content': eval_script_content,
        'eval_output': eval_output,
    }
    if obs.exit_code != 0 and obs.exit_code != 124:
        logger.warning(f'Evaluation script failed with exit code {obs.exit_code}')
        logger.warning(f'Output: {eval_output}')
        outputs['success'] = int(
            'KeyboardInterrupt' in eval_output
        )  # super-dainiu: assume ``KeyboardInterrupt`` is a success as is done in ML-Bench

    else:
        logger.info(f'Evaluation script succeeded with exit code {obs.exit_code}')
        logger.info(f'Output: {eval_output}')
        outputs['success'] = 1
    outputs['eval_exit_code'] = obs.exit_code

    logger.info(f"{'-' * 50} END Runtime Completion Fn {'-' * 50}")
    return outputs


def process_instance(instance: Any, metadata: EvalMetadata, reset_logger: bool = True):
    config = get_config(metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance['instance_id'], log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance["instance_id"]}.')

    repo_url = instance['github']
    repo_name = repo_url.split('/')[-1]
    task_path = os.path.join('/workspace', repo_name, instance['path'][2:])
    # Prepare the task instruction
    instruction = (
        f'Please complete the Machine Learning task in the following repository: {repo_name}\n\n'
        f'{instance["instruction"]}\n\n'
        'You should create a script named `run.sh` under the specified path in the repo to run the task.\n\n'
        f'You can find the task repo at: {task_path}\n\n'
        + (
            'Here is the prefix code for the task:\n'
            '```bash\n'
            f'{instance["prefix_code"]}\n'
            '```\n\n'
            if instance['prefix_code']
            else ''
        )
        + 'You should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).'
    )
    instruction += AGENT_CLS_TO_INST_SUFFIX[metadata.agent_class]

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    initialize_runtime(runtime, instance)

    # Run the agent
    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=MessageAction(content=instruction),
            runtime=runtime,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                metadata.agent_class
            ),
        )
    )
    assert state is not None
    metrics = state.metrics.get() if state.metrics else {}

    test_result = complete_runtime(runtime)

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=instance['instance_id'],
        instance=instance.to_dict(),
        instruction=instruction,
        metadata=metadata,
        history=histories,
        test_result=test_result,
        metrics=metrics,
    )
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '-s',
        '--eval-split',
        type=str,
        default='quarter',
        choices=['full', 'quarter'],
        help='data split to evaluate on, either full or quarter',
    )
    args, _ = parser.parse_known_args()

    data_split = args.eval_split

    ml_bench = load_dataset('super-dainiu/ml-bench', split=data_split).to_pandas()
    ml_bench.rename(columns={'id': 'instance_id'}, inplace=True)

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        f'ml-bench-{data_split}',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(ml_bench, output_file, args.eval_n_limit)

    run_evaluation(
        instances, metadata, output_file, args.eval_num_workers, process_instance
    )
