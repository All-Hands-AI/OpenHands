import asyncio
import os
import re

import nltk
import pandas as pd
from datasets import load_dataset

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    compatibility_for_eval_history_pairs,
    get_default_sandbox_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    OpenHandsConfig,
    get_llm_config_arg,
    parse_arguments,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import MessageAction
from openhands.utils.async_utils import call_async_from_sync

# Only CodeActAgent can delegate to BrowsingAgent
SUPPORTED_AGENT_CLS = {'CodeActAgent'}


def get_config(
    metadata: EvalMetadata,
) -> OpenHandsConfig:
    assert metadata.max_iterations == 1, (
        'max_iterations must be 1 for browsing delegation evaluation.'
    )
    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'python:3.12-bookworm'
    config = OpenHandsConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=sandbox_config,
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.enable_prompt_extensions = False
    return config


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(metadata)
    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    instruction = (
        f'You can delegate browsing tasks to a browser agent. '
        f"For example, for query 'Who is the president of the United States?', you can delegate the task to a browser agent via <execute_browse> Who is the president of the United States? </execute_browse>.\n"
        f'Now, solve the following query: "{instance.instruction}"\n'
        f'NOTE: You should copy the "query" as is into the <execute_browse> tag. DO NOT change ANYTHING in the query.'
    )

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)

    state: State | None = asyncio.run(
        run_controller(
            config=config,
            initial_user_action=MessageAction(content=instruction),
            runtime=runtime,
        )
    )

    if state is None:
        raise ValueError('State should not be None.')

    metrics = state.metrics.get() if state.metrics else None
    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # find the last delegate action
    last_delegate_action = None
    result = {}
    for action, _ in histories:
        if action['action'] == 'delegate':
            last_delegate_action = action
            instruction_for_delegate = action['args']['inputs']['task']
            # parse `browse_actions` from `instruction_for_delegate`
            # task = f'{thought}. I should start with: {browse_actions}'
            instruction_for_delegate = re.search(
                r'I should start with: (.*)', instruction_for_delegate
            ).group(1)

            # calculate the edit distance between the instance.instruction and the instruction_for_delegate
            edit_distance = nltk.edit_distance(
                instance.instruction, instruction_for_delegate
            )
            is_exact_match = (
                instance.instruction.strip() == instruction_for_delegate.strip()
            )
            result['edit_distance'] = edit_distance
            result['is_exact_match'] = is_exact_match

    # Save the output
    output = EvalOutput(
        instance_id=instance.instance_id,
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result={
            'query': instance.instruction,
            'action': last_delegate_action,
            'result': result,
        },
    )
    return output


if __name__ == '__main__':
    args = parse_arguments()

    dataset = load_dataset('OpenHands/eval-browsing-instructions')
    dataset = dataset['train'].to_pandas()
    assert dataset.columns.tolist() == ['instance_id', 'instruction']

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accuracy of results
        llm_config.modify_params = False

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'browsing_delegation',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )

    if metadata.agent_class not in SUPPORTED_AGENT_CLS:
        raise ValueError(
            f'Agent class {metadata.agent_class} not supported with AgentDelegation.'
        )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(dataset, output_file, args.eval_n_limit)
    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
    )
