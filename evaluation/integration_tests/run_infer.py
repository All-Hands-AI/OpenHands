import asyncio
import importlib.util
import os

import pandas as pd

from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    get_default_sandbox_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
    update_llm_config_for_completions_logging,
)
from evaluation.utils.shared import (
    codeact_user_response as fake_user_response,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AgentConfig,
    OpenHandsConfig,
    get_llm_config_arg,
    parse_arguments,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import MessageAction
from openhands.events.serialization.event import event_to_dict
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

FAKE_RESPONSES = {
    'CodeActAgent': fake_user_response,
    'VisualBrowsingAgent': fake_user_response,
}


def get_config(
    metadata: EvalMetadata,
    instance_id: str,
) -> OpenHandsConfig:
    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.platform = 'linux/amd64'
    config = OpenHandsConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime=os.environ.get('RUNTIME', 'docker'),
        max_iterations=metadata.max_iterations,
        sandbox=sandbox_config,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
        # debug
        debug=True,
    )
    config.set_llm_config(
        update_llm_config_for_completions_logging(
            metadata.llm_config, metadata.eval_output_dir, instance_id
        )
    )
    agent_config = AgentConfig(
        enable_jupyter=True,
        enable_browsing=True,
        enable_llm_editor=False,
    )
    config.set_agent_config(agent_config)
    return config


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(metadata, instance.instance_id)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, str(instance.instance_id), log_dir)
    else:
        logger.info(
            f'\nStarting evaluation for instance {str(instance.instance_id)}.\n'
        )

    # =============================================
    # import test instance
    # =============================================
    instance_id = instance.instance_id
    spec = importlib.util.spec_from_file_location(instance_id, instance.file_path)
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)
    assert hasattr(test_module, 'Test'), (
        f'Test module {instance_id} does not have a Test class'
    )

    test_class: type[BaseIntegrationTest] = test_module.Test
    assert issubclass(test_class, BaseIntegrationTest), (
        f'Test class {instance_id} does not inherit from BaseIntegrationTest'
    )

    instruction = test_class.INSTRUCTION

    # =============================================
    # create sandbox and run the agent
    # =============================================
    runtime: Runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    try:
        test_class.initialize_runtime(runtime)

        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        state: State | None = asyncio.run(
            run_controller(
                config=config,
                initial_user_action=MessageAction(content=instruction),
                runtime=runtime,
                fake_user_response_fn=FAKE_RESPONSES[metadata.agent_class],
            )
        )
        if state is None:
            raise ValueError('State should not be None.')

        # # =============================================
        # # result evaluation
        # # =============================================

        histories = state.history

        # some basic check
        logger.info(f'Total events in history: {len(histories)}')
        assert len(histories) > 0, 'History should not be empty'

        test_result: TestResult = test_class.verify_result(runtime, histories)
        metrics = state.metrics.get() if state.metrics else None
    finally:
        runtime.close()

    # Save the output
    output = EvalOutput(
        instance_id=str(instance.instance_id),
        instance=instance.to_dict(),
        instruction=instruction,
        metadata=metadata,
        history=[event_to_dict(event) for event in histories],
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result=test_result.model_dump(),
    )
    return output


def load_integration_tests() -> pd.DataFrame:
    """Load tests from python files under ./tests"""
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(cur_dir, 'tests')
    test_files = [
        os.path.join(test_dir, f)
        for f in os.listdir(test_dir)
        if f.startswith('t') and f.endswith('.py')
    ]
    df = pd.DataFrame(test_files, columns=['file_path'])
    df['instance_id'] = df['file_path'].apply(
        lambda x: os.path.basename(x).rstrip('.py')
    )
    return df


if __name__ == '__main__':
    args = parse_arguments()
    integration_tests = load_integration_tests()

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'integration_tests',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')

    # Parse dataset IDs if provided
    eval_ids = None
    if args.eval_ids:
        eval_ids = str(args.eval_ids).split(',')
        logger.info(f'\nUsing specific dataset IDs: {eval_ids}\n')

    instances = prepare_dataset(
        integration_tests,
        output_file,
        args.eval_n_limit,
        eval_ids=eval_ids,
    )

    run_evaluation(
        instances,
        metadata,
        output_file,
        args.eval_num_workers,
        process_instance,
    )

    df = pd.read_json(output_file, lines=True, orient='records')

    # record success and reason
    df['success'] = df['test_result'].apply(lambda x: x['success'])
    df['reason'] = df['test_result'].apply(lambda x: x['reason'])
    logger.info('-' * 100)
    logger.info(
        f'Success rate: {df["success"].mean():.2%} ({df["success"].sum()}/{len(df)})'
    )
    logger.info(
        '\nEvaluation Results:'
        + '\n'
        + df[['instance_id', 'success', 'reason']].to_string(index=False)
    )
    logger.info('-' * 100)

    # record cost for each instance, with 3 decimal places
    # we sum up all the "costs" from the metrics array
    df['cost'] = df['metrics'].apply(
        lambda m: round(sum(c['cost'] for c in m['costs']), 3)
        if m and 'costs' in m
        else 0.0
    )

    # capture the top-level error if present, per instance
    df['error_message'] = df.get('error', None)

    logger.info(f'Total cost: USD {df["cost"].sum():.2f}')

    report_file = os.path.join(metadata.eval_output_dir, 'report.md')
    with open(report_file, 'w') as f:
        f.write(
            f'Success rate: {df["success"].mean():.2%}'
            f' ({df["success"].sum()}/{len(df)})\n'
        )
        f.write(f'\nTotal cost: USD {df["cost"].sum():.2f}\n')
        f.write(
            df[
                ['instance_id', 'success', 'reason', 'cost', 'error_message']
            ].to_markdown(index=False)
        )
