import asyncio
import copy
import json
import os
from collections import defaultdict
from zipfile import ZipFile

import pandas as pd
from datasets import load_dataset

import openhands.agenthub
from evaluation.benchmarks.swe_bench.run_infer import (
    AGENT_CLS_TO_FAKE_USER_RESPONSE_FN,
    _get_swebench_workspace_dir_name,
    complete_runtime,
    filter_dataset,
    get_config,
    get_instruction,
    initialize_runtime,
)
from evaluation.utils.shared import (
    EvalException,
    EvalMetadata,
    EvalOutput,
    get_metrics,
    is_fatal_evaluation_error,
    make_metadata,
    reset_logger_for_multiprocessing,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    get_llm_config_arg,
    get_parser,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import (
    CmdRunAction,
    MessageAction,
)
from openhands.events.observation import (
    CmdOutputObservation,
)
from openhands.events.serialization.event import event_to_dict
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync


def initialize_runtime_for_memory_files(
    runtime: Runtime,
    instance: pd.Series,
):
    workspace_dir_name = _get_swebench_workspace_dir_name(instance)
    # if memory_files_dir is not None, copy it to /workspace/{workspace_dir_name}/.openhands/memory
    if 'memory_files_dir' in instance and instance['memory_files_dir'] is not None:
        runtime.copy_to(
            instance['memory_files_dir'],
            f'/workspace/{workspace_dir_name}/.openhands/memory',
            recursive=True,
        )

        action = CmdRunAction(
            command='ls -la /workspace/{workspace_dir_name}/.openhands/memory'
        )
        action.set_hard_timeout(600)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})


def complete_runtime_for_memory_files(
    runtime: Runtime,
    instance: pd.Series,
    metadata: EvalMetadata,
):
    workspace_dir_name = _get_swebench_workspace_dir_name(instance)

    # Get the .openhands/memory directory if it exists
    memory_zip_file = None

    # Check if the memory directory exists
    action = CmdRunAction(
        command=f'ls -la /workspace/{workspace_dir_name}/.openhands/memory'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    memory_files_dir = None
    if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
        logger.info('Memory directory exists, copying as zip')

        # Copy the zipped memory directory
        temp_zip = runtime.copy_from(
            f'/workspace/{workspace_dir_name}/.openhands/memory'
        )
        memory_zip_file = temp_zip
        logger.info(f'Copied memory zip to temporary location: {memory_zip_file}')
        # unzip to metadata.eval_output_dir / "memory_files" / instance_id / memory.zip
        memory_files_dir = os.path.join(
            metadata.eval_output_dir, 'memory_files', instance['instance_id']
        )
        os.makedirs(memory_files_dir, exist_ok=True)
        with ZipFile(memory_zip_file, 'r') as zip_ref:
            zip_ref.extractall(memory_files_dir)
        logger.info(f'Unzipped memory zip to {memory_files_dir}')
    else:
        logger.warning(f'Failed to create memory.zip: {str(obs)}')
    return memory_files_dir


def process_instance_with_memory(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
    runtime_failure_count: int = 0,
) -> EvalOutput:
    config = get_config(instance, metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    # Increase resource_factor with increasing attempt_id
    if runtime_failure_count > 0:
        config.sandbox.remote_runtime_resource_factor = min(
            config.sandbox.remote_runtime_resource_factor * (2**runtime_failure_count),
            8,
        )
        logger.warning(
            f'This is the {runtime_failure_count + 1}th attempt for instance {instance.instance_id}, setting resource factor to {config.sandbox.remote_runtime_resource_factor}'
        )

    metadata = copy.deepcopy(metadata)
    metadata.details['runtime_failure_count'] = runtime_failure_count
    metadata.details['remote_runtime_resource_factor'] = (
        config.sandbox.remote_runtime_resource_factor
    )

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)

    try:
        initialize_runtime(runtime, instance)
        initialize_runtime_for_memory_files(runtime, instance)

        instruction = get_instruction(instance, metadata)

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State | None = asyncio.run(
            run_controller(
                config=config,
                initial_user_action=MessageAction(content=instruction),
                runtime=runtime,
                fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN[
                    metadata.agent_class
                ],
            )
        )

        # if fatal error, throw EvalError to trigger re-run
        if is_fatal_evaluation_error(state.last_error):
            raise EvalException('Fatal error detected: ' + state.last_error)

        # ======= THIS IS SWE-Bench specific =======
        # Get git patch
        return_val = complete_runtime(runtime, instance)
        memory_files_dir = complete_runtime_for_memory_files(
            runtime, instance, metadata
        )
        git_patch = return_val['git_patch']
        repo_md = return_val['repo_md']

        logger.info(
            f'Got git diff for instance {instance.instance_id}:\n--------\n{git_patch}\n--------'
        )
        logger.info(
            f'Got repo.md for instance {instance.instance_id}:\n--------\n{repo_md}\n--------'
        )

    finally:
        runtime.close()
    # ==========================================

    # ======= Attempt to evaluate the agent's edits =======
    # we use eval_infer.sh to evaluate the agent's edits, not here
    # because the agent may alter the environment / testcases
    test_result = {
        'git_patch': git_patch,
        'repo_md': repo_md,
        'memory_files_dir': memory_files_dir,
    }

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.
    if state is None:
        raise ValueError('State should not be None.')

    # NOTE: this is NO LONGER the event stream, but an agent history that includes delegate agent's events
    histories = [event_to_dict(event) for event in state.history]
    metrics = get_metrics(state)

    # Save the output
    output = EvalOutput(
        instance_id=instance.instance_id,
        instruction=instruction,
        instance=instance.to_dict(),  # SWE Bench specific
        test_result=test_result,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
    )
    return output


def run_sequential_evaluation(
    dataset: pd.DataFrame,
    metadata: EvalMetadata,
    output_file: str,
    process_instance_func: callable,
    max_retries: int = 5,
):
    """
    Run evaluation sequentially for instances grouped by repository.

    1. First sort by instance_ids, split them by __ and take the first element as "repo"
    2. Group instance_ids by repo, and then sort them by order
    3. Run the evaluation for each instance in each repo one by one
    4. The first instance id of a repo will start WITHOUT any repo md
       The repo md generated by the first instance will be fed to the evaluation of the second instance
    """
    # Extract repo from instance_id and add as a column
    dataset['repo'] = dataset['instance_id'].apply(lambda x: x.split('__')[0])

    # Group by repo and sort within each group
    repo_groups = defaultdict(list)
    for _, instance in dataset.iterrows():
        repo_groups[instance['repo']].append(instance)

    # Sort instances within each repo group
    for repo in repo_groups:
        repo_groups[repo] = sorted(repo_groups[repo], key=lambda x: x['instance_id'])

    # Process instances sequentially by repo
    total_instances = len(dataset)
    processed_count = 0

    instance_id_to_repo_md = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as input_fp:
            for line in input_fp:
                result = EvalOutput.model_validate_json(line)
                instance_id_to_repo_md[result.instance_id] = result.test_result[
                    'repo_md'
                ]

    # Open output file for writing results
    output_fp = open(output_file, 'a')

    try:
        # Process each repo group sequentially
        for repo, instances in repo_groups.items():
            logger.info(
                f'Processing repository: {repo} with {len(instances)} instances'
            )

            # Track repo_md across instances in the same repo
            current_repo_md = None

            # Process each instance in the repo sequentially
            for i, instance in enumerate(instances):
                instance_series = pd.Series(instance)

                if instance_series['instance_id'] in instance_id_to_repo_md:
                    # Skip if the instance has already been processed
                    _repo_md = instance_id_to_repo_md[instance_series['instance_id']]
                    if _repo_md is not None and _repo_md.strip() != '':
                        current_repo_md = _repo_md
                    logger.info(
                        f'Skipping instance {instance_series["instance_id"]} because it has already been processed'
                    )
                    processed_count += 1
                    continue

                # Set repo_md from previous instance if available
                if i > 0 and current_repo_md is not None:
                    instance_series['repo_md'] = current_repo_md
                else:
                    instance_series['repo_md'] = None

                # Process the instance
                logger.info(
                    f"Processing instance {instance_series['instance_id']} ({processed_count + 1}/{total_instances})"
                )
                logger.info(
                    f'Repo.md for instance {instance_series["instance_id"]}: {instance_series["repo_md"]}'
                )

                # Try processing with retries
                retry_count = 0
                result = None

                while retry_count < max_retries:
                    try:
                        # Process the instance
                        result: EvalOutput = process_instance_func(
                            instance=instance_series,
                            metadata=metadata,
                            reset_logger=False,
                            runtime_failure_count=retry_count,
                        )

                        # If successful, break out of retry loop
                        if result is not None:
                            break
                    except Exception as e:
                        logger.error(
                            f"Error processing instance {instance_series['instance_id']}: {str(e)}"
                        )
                        if is_fatal_evaluation_error(str(e)):
                            logger.error(f'Fatal error encountered: {str(e)}')
                            break

                        # Increment retry count and try again
                        retry_count += 1
                        logger.info(
                            f"Retrying instance {instance_series['instance_id']} (attempt {retry_count + 1}/{max_retries})"
                        )

                # Write result to output file
                if result is not None:
                    # Extract repo_md from the result for the next instance
                    if result.test_result and 'repo_md' in result.test_result:
                        current_repo_md = result.test_result['repo_md']
                        logger.info(
                            f'Extracted repo_md for next instance in {repo}: {current_repo_md}'
                        )

                    # Write result to output file
                    output_fp.write(result.model_dump_json() + '\n')
                    output_fp.flush()

                processed_count += 1
                logger.info(
                    f"Completed instance {instance_series['instance_id']} ({processed_count}/{total_instances})"
                )

    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received. Cleaning up...')

    finally:
        output_fp.close()

    logger.info('Sequential evaluation completed')


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        default='princeton-nlp/SWE-bench',
        help='data set to evaluate on, either full-test or lite-test',
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        help='split to evaluate on',
    )
    args, _ = parser.parse_known_args()

    # Load dataset from huggingface
    dataset = load_dataset(args.dataset, split=args.split)
    swe_bench_tests = filter_dataset(dataset.to_pandas(), 'instance_id')
    logger.info(
        f'Loaded dataset {args.dataset} with split {args.split}: {len(swe_bench_tests)} tasks'
    )

    # Filter for SWE-Gym verified instances if needed
    if 'SWE-Gym' in args.dataset:
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'split',
                'swegym_verified_instances.json',
            ),
            'r',
        ) as f:
            swegym_verified_instances = json.load(f)
            swe_bench_tests = swe_bench_tests[
                swe_bench_tests['instance_id'].isin(swegym_verified_instances)
            ]
        logger.info(
            f'{len(swe_bench_tests)} tasks left after filtering for SWE-Gym verified instances'
        )

    # Get LLM config
    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        llm_config.log_completions = True
        # modify_params must be False for evaluation purpose, for reproducibility and accuracy of results
        llm_config.modify_params = False

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    # Set up metadata
    details = {}
    _agent_cls = openhands.agenthub.Agent.get_cls(args.agent_cls)

    dataset_description = (
        args.dataset.replace('/', '__') + '-' + args.split.replace('/', '__')
    )
    metadata = make_metadata(
        llm_config,
        dataset_description,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
        details=details,
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    print(f'### OUTPUT FILE: {output_file} ###')

    instance_ids = sorted(swe_bench_tests['instance_id'].tolist())
    selected_instance_ids = instance_ids[: args.eval_n_limit]

    instances = swe_bench_tests[
        swe_bench_tests['instance_id'].isin(selected_instance_ids)
    ]
    if len(instances) > 0 and not isinstance(
        instances['PASS_TO_PASS'][instances['PASS_TO_PASS'].index[0]], str
    ):
        for col in ['PASS_TO_PASS', 'FAIL_TO_PASS']:
            instances[col] = instances[col].apply(lambda x: str(x))
    # We will do the filtering in the run_sequential_evaluation function

    logger.info(
        f'Running sequential evaluation for {len(instances)} instances: {instances["instance_id"].tolist()}'
    )
    # Run sequential evaluation
    run_sequential_evaluation(
        instances,
        metadata,
        output_file,
        process_instance_with_memory,
        max_retries=5,
    )
