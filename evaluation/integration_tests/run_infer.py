import asyncio
import importlib.util
import os

import pandas as pd

from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
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
    parse_arguments,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import MessageAction
from openhands.runtime.base import Runtime

FAKE_RESPONSES = {
    'CodeActAgent': codeact_user_response,
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
            # use default base_container_image
            enable_auto_lint=True,
            use_host_network=False,
            timeout=100,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
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
    assert hasattr(
        test_module, 'Test'
    ), f'Test module {instance_id} does not have a Test class'

    test_class: type[BaseIntegrationTest] = test_module.Test
    assert issubclass(
        test_class, BaseIntegrationTest
    ), f'Test class {instance_id} does not inherit from BaseIntegrationTest'

    instruction = test_class.INSTRUCTION

    # =============================================
    # create sandbox and run the agent
    # =============================================

    runtime: Runtime = create_runtime(config)

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

    histories = state.history.get_events()
    test_result: TestResult = test_class.verify_result(runtime, histories)
    metrics = state.metrics.get() if state.metrics else None

    # Save the output
    output = EvalOutput(
        instance_id=str(instance.instance_id),
        instance=instance.to_dict(),
        instruction=instruction,
        metadata=metadata,
        history=histories,
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
