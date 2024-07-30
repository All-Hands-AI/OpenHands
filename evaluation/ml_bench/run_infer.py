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
import logging
import os
import pathlib
from typing import Any

from datasets import load_dataset

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
from opendevin.runtime.docker.ssh_box import DockerSSHBox

config = load_app_config()

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have completed the task, please run the following command: <execute_bash> exit </execute_bash>.\n'
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


def process_instance(instance: Any, metadata: EvalMetadata, reset_logger: bool = True):
    agent = Agent.get_cls(metadata.agent_class)(llm=LLM(config=metadata.llm_config))
    old_workspace_mount_path = config.workspace_mount_path
    old_workspace_base = config.workspace_base
    try:
        workspace_mount_path = os.path.join(
            config.workspace_mount_path, '_eval_workspace'
        )
        # create process-specific workspace dir
        # so that different agent don't interfere with each other.
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

        # reset workspace to config
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
        if reset_logger:
            # Set up logger
            log_file = os.path.join(
                metadata.eval_output_dir,
                'logs',
                f"instance_{instance['id']}_pid_{os.getpid()}.log",
            )
            # Remove all existing handlers from logger
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # add back the console handler to print ONE line
            logger.addHandler(get_console_handler())
            logger.info(
                f"Starting evaluation for instance {instance['id']}.\nLOG:   tail -f {log_file}"
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

        # Create a sandbox, using the instance ID and PID as the session ID to avoid conflicts
        sid = str(instance['id']) + '_' + str(os.getpid())
        sandbox = DockerSSHBox(
            config=config.sandbox,
            persist_sandbox=False,
            workspace_mount_path=config.workspace_mount_path,
            sandbox_workspace_dir=config.workspace_mount_path_in_sandbox,
            cache_dir=config.cache_dir,
            run_as_devin=config.run_as_devin,
            sid=sid,
        )

        # Set up the task environment
        sandbox.execute(f'conda activate {ID2CONDA[instance["github_id"]]}')

        # Clone the task repo into the sandbox
        repo_url = instance['github']
        repo_name = repo_url.split('/')[-1]
        sandbox.execute(f'git clone {repo_url} /workspace/{repo_name}')
        sandbox.execute(f'chmod -R 777 /workspace/{repo_name}')

        # Navigate to the task's code path
        task_path = os.path.join('/workspace', repo_name, instance['path'][2:])
        sandbox.execute(f'cd {task_path}')

        # Prepare the task instruction
        instruction = (
            f'Please complete the Machine Learning task in the following repository: {repo_name}\n\n'
            f'The task is: {instance["task"]}\n\n'
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
        instruction += AGENT_CLS_TO_INST_SUFFIX[agent.__class__.__name__]

        # Run the agent
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
        assert state is not None
        metrics = state.metrics.get() if state.metrics else {}

        # Evaluate the agent's script
        eval_script = os.path.join(task_path, 'run.sh')
        logger.info(f'Running evaluation script: {eval_script}')

        try:
            _, eval_script_content = sandbox.execute(f'cat {eval_script}')
        except Exception as e:
            logger.error(f'Error reading evaluation script: {e}')
            eval_script_content = ''

        try:
            exit_code, eval_output = sandbox.execute(
                f'timeout 120s conda run -n {ID2CONDA[instance["github_id"]]} bash {eval_script}',
                timeout=600,
            )
        except Exception as e:
            logger.error(f'Error running evaluation script: {e}')
            exit_code = -1
            eval_output = ''

        if exit_code != 0 and exit_code != 124:
            logger.warning(f'Evaluation script failed with exit code {exit_code}')
            logger.warning(f'Output: {eval_output}')
            metrics['success'] = int(
                'KeyboardInterrupt' in eval_output
            )  # super-dainiu: assume ``KeyboardInterrupt`` is a success as is done in ML-Bench
        else:
            logger.info(f'Evaluation script succeeded with exit code {exit_code}')
            logger.info(f'Output: {eval_output}')
            metrics['success'] = 1

        # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
        # for compatibility with the existing output format, we can remake the pairs here
        # remove when it becomes unnecessary
        histories = state.history.compatibility_for_eval_history_pairs()

        # Save the output
        output = {
            'instance_id': instance['id'],
            'repo': repo_url,
            'instruction': instruction,
            'metadata': metadata.model_dump(),
            'history': histories,
            'eval_script': eval_script_content,
            'eval_exit_code': exit_code,
            'eval_output': eval_output,
            'metrics': metrics,
        }

    except Exception as e:
        logger.error(f'Error processing instance {instance["id"]}: {e}')
        raise
    finally:
        config.workspace_mount_path = old_workspace_mount_path
        config.workspace_base = old_workspace_base

    # Shutdown the sandbox
    sandbox.close()
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

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    ml_bench = load_dataset('super-dainiu/ml-bench', split=data_split).to_pandas()

    id_column = 'instance_id'
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
    instances = prepare_dataset(ml_bench, output_file, args.eval_n_limit, id_column)

    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
        id_column,
    )
