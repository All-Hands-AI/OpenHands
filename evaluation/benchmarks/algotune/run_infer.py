import asyncio
import functools
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    compatibility_for_eval_history_pairs,
    get_default_sandbox_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
    update_llm_config_for_completions_logging,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AgentConfig,
    OpenHandsConfig,
    get_agent_config_arg,
    get_evaluation_parser,
    get_llm_config_arg,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import CmdRunAction, MessageAction
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync


def discover_tasks():
    """Automatically discover all available tasks by scanning directories."""
    script_dir = Path(__file__).parent
    tasks_dir = script_dir / 'tasks'
    tasks = {}

    if not tasks_dir.exists():
        return tasks

    for item in tasks_dir.iterdir():
        if (
            item.is_dir()
            and not item.name.startswith('.')
            and not item.name.startswith('__')
        ):
            # Check if it's a valid task directory
            evaluate_file = item / 'evaluator.py'
            test_outputs_file = item / 'test_outputs.py'
            solver_file = item / 'solution.sh'

            if all(f.exists() for f in [solver_file, evaluate_file, test_outputs_file]):
                tasks[item.name] = str(item)

    return tasks


def algotune_user_response(state, runtime: Runtime, **kwargs):
    """User response function for algorithm optimization training with iterative feedback."""
    base_msg = 'Please continue on whatever approach you think is suitable.\nIf you think you have solved the task, please finish the interaction.'
    base_msg += '\n\nIMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'

    return base_msg


def get_config(
    metadata: EvalMetadata, workspace_id: str = None, enable_volumes: bool = True
) -> OpenHandsConfig:
    """Configure OpenHands for algorithm optimization evaluation."""

    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.timeout = 600  # Set execution timeout to 10 minutes
    sandbox_config.remote_runtime_api_timeout = 600
    sandbox_config.base_container_image = 'linhaowei1/algotune-openhands:v0.0.2'
    sandbox_config.use_host_network = True
    sandbox_config.enable_auto_lint = True

    # Set volumes based on enable_volumes parameter
    if enable_volumes:
        # Create unique workspace directory for the entire experiment
        if workspace_id:
            workspace_dir = os.path.join(
                os.getcwd(), 'external', 'algotune', workspace_id
            )
            os.makedirs(workspace_dir, exist_ok=True)
            sandbox_config.volumes = f'{workspace_dir}:/workspace:rw'
            logger.info(
                f'Created workspace directory for {workspace_id}: {workspace_dir}'
            )
        else:
            sandbox_config.volumes = 'external:/workspace:rw'
    else:
        sandbox_config.volumes = None
        logger.info('Volumes disabled - container will not have persistent storage')

    # Set unique container labels for complete isolation
    if workspace_id:
        container_labels = {
            'algotune.experiment_id': workspace_id,
            'algotune.model': metadata.llm_config.model.replace('/', '_').replace(
                ':', '_'
            ),
            'algotune.agent': metadata.agent_class,
            'algotune.pid': str(os.getpid()),
            'algotune.timestamp': str(int(datetime.now().timestamp())),
        }
    else:
        container_labels = {
            'algotune.experiment_id': 'default',
            'algotune.pid': str(os.getpid()),
            'algotune.timestamp': str(int(datetime.now().timestamp())),
        }

    sandbox_config.docker_runtime_kwargs = {'labels': container_labels}
    logger.info(f'Container labels: {container_labels}')

    config = OpenHandsConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=sandbox_config,
        workspace_base=None,
        workspace_mount_path=None,
        debug=True,
    )

    # Set up LLM config with logging
    config.set_llm_config(
        update_llm_config_for_completions_logging(
            metadata.llm_config, metadata.eval_output_dir, workspace_id or 'default'
        )
    )

    # Set up agent config
    agent_config = AgentConfig(
        enable_jupyter=False,
        enable_browsing=False,
        enable_mcp=False,
        condenser=metadata.condenser_config,
        enable_prompt_extensions=False,
    )
    config.set_agent_config(agent_config)
    return config


def initialize_runtime(runtime: Runtime, task_name: str):
    """Initialize the runtime for algorithm optimization training."""
    logger.info(f'{"-" * 50} BEGIN Runtime Initialization {"-" * 50}')

    # Create workspace directory
    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    # Copy task-specific files
    task_dir = f'evaluation/benchmarks/algotune/tasks/{task_name}'

    # Copy evaluation script
    eval_path = f'{task_dir}/evaluator.py'
    runtime.copy_to(eval_path, '/workspace/')

    # Copy test outputs script
    test_outputs_path = f'{task_dir}/test_outputs.py'
    runtime.copy_to(test_outputs_path, '/workspace/')

    logger.info(f'Initialized runtime with data directory for {task_name}')
    logger.info(f'{"-" * 50} END Runtime Initialization {"-" * 50}')


def _backup_solver_code(runtime: Runtime) -> str:
    """Reads the content of the solver.py file from the runtime."""
    try:
        # Use run_action to cat the file content
        action = CmdRunAction(command='cat /workspace/solver.py')
        obs = runtime.run_action(action)
        if obs.exit_code == 0:
            return obs.content
        else:
            return f'Error reading solver file: {obs.content}'
    except Exception as e:
        return f'Failed to backup solver code: {str(e)}'


def _parse_evaluation_output(output: str) -> dict[str, Any]:
    """Parses the complex output from the run-tests.sh script."""
    results = {
        'target_speedup': 0.0,
        'solver_speedup': 0.0,
        'validity': False,
        'passed_tests': [],
        'failed_tests': [],  # Assuming future need
        'error': 'None',
    }

    try:
        # Extract Target Speedup from the entire output
        target_speedup_match = re.search(
            r'--- TARGET SPEEDUP ---\s*([\d.]+)\s*--- TARGET SPEED END ---', output
        )
        if target_speedup_match:
            results['target_speedup'] = float(target_speedup_match.group(1))

        logger.info(f'Target speedup: {results["target_speedup"]}')

        # Isolate the final validation section to parse solver stats and test results
        if 'Running final validation on original solver...' not in output:
            results['error'] = 'Final validation section not found in output.'
            results['validity'] = False
            return results

        final_validation_section = output.split(
            'Running final validation on original solver...'
        )[-1]
        logger.info(f'Final validation section: {final_validation_section}')
        # The second performance summary block relates to the final solver's stats
        perf_summary_match = re.search(
            r'--- Performance Summary ---\s*'
            r'Validity: (True|False)\s*'
            r'.*?'  # Non-greedy match for lines between
            r'Calculated Speedup:\s*([\d.]+) x',
            final_validation_section,  # Search only in the final section
            re.DOTALL,
        )
        if perf_summary_match:
            results['solver_speedup'] = float(perf_summary_match.group(2))
        logger.info(f'Solver speedup: {results["solver_speedup"]}')
        # Extract passed tests from the final validation block
        passed_tests = re.findall(r'PASSED\s+([^\n]+)', final_validation_section)
        results['passed_tests'] = [test.strip() for test in passed_tests]
        logger.info(f'Passed tests: {results["passed_tests"]}')
        # Determine overall validity based on the final test run summary

        summary_line_match = re.search(
            r'={2,}\s(\d+\spassed.*)\s={2,}', final_validation_section
        )
        if summary_line_match:
            summary_line = summary_line_match.group(1).strip()
            logger.info(f'Summary line: {summary_line}')
            # If the summary contains "failed" or "errors", it's not valid.
            if (
                'failed' not in summary_line
                and 'errors' not in summary_line
                and 'passed' in summary_line
            ):
                results['validity'] = True
            else:
                results['error'] = f'Final validation failed: {summary_line}'
        else:
            results['error'] = 'Could not parse final test summary.'
            results['validity'] = False

    except Exception as e:
        results['error'] = f'Failed to parse output: {str(e)}'
        results['validity'] = False

    return results


def evaluate_test_cases(runtime: Any, task_name: str) -> dict[str, Any]:
    """Evaluate the final solution on test instances using the evaluator.py script."""
    logger.info(f'{"-" * 50} BEGIN Test Instance Evaluation {"-" * 50}')

    backup_solver_code = _backup_solver_code(runtime)

    # Prepare and run the evaluation script
    task_dir = f'evaluation/benchmarks/algotune/tasks/{task_name}'
    eval_script_path = f'{task_dir}/run-tests.sh'
    runtime.copy_to(eval_script_path, '/workspace/')

    action = CmdRunAction(command='cd /workspace && bash run-tests.sh', blocking=True)
    action.set_hard_timeout(600)

    test_results = []
    summary = {}

    try:
        obs = runtime.run_action(action)
        full_output = obs.content

        if obs.exit_code == 0:
            parsed_data = _parse_evaluation_output(full_output)
            test_result = {
                'instance_id': f'{task_name}_test',
                'valid': parsed_data['validity'],
                'score': parsed_data[
                    'solver_speedup'
                ],  # Main score is the achieved speedup
                'target_speedup': parsed_data['target_speedup'],
                'passed_tests': parsed_data['passed_tests'],
                'error': parsed_data['error'],
                'solver_code': backup_solver_code,
                'timestamp': datetime.now().isoformat(),
                'evaluation_output': full_output,
            }
        else:
            # Evaluation script itself failed to run
            test_result = {
                'instance_id': f'{task_name}_test',
                'valid': False,
                'score': 0.0,
                'target_speedup': 0.0,
                'passed_tests': [],
                'error': f'Evaluation script failed with exit code {obs.exit_code}: {full_output}',
                'solver_code': backup_solver_code,
                'timestamp': datetime.now().isoformat(),
                'evaluation_output': full_output,
            }
        test_results.append(test_result)

    except Exception as e:
        test_result = {
            'instance_id': f'{task_name}_test',
            'valid': False,
            'score': 0.0,
            'target_speedup': 0.0,
            'passed_tests': [],
            'error': f'Unexpected error during evaluation: {str(e)}',
            'solver_code': backup_solver_code,
            'timestamp': datetime.now().isoformat(),
            'evaluation_output': 'Execution failed before output could be captured.',
        }
        test_results.append(test_result)

    # Log detailed progress
    for res in test_results:
        status = '✓ PASSED' if res['valid'] else '✗ FAILED'
        logger.info(f'Test evaluation {status} for instance {res["instance_id"]}')
        logger.info(
            f'  Solver Speedup: {res["score"]:.2f}x, Target Speedup: {res["target_speedup"]:.2f}x'
        )
        if res['valid']:
            logger.info(
                f'  Passed Tests ({len(res["passed_tests"])}): {", ".join(res["passed_tests"])}'
            )
        else:
            logger.info(f'  Error: {res["error"]}')

    # Calculate summary statistics
    valid_results = [r for r in test_results if r['valid']]
    summary = {
        'total_test_instances': len(test_results),
        'valid_solutions': len(valid_results),
        'test_results': test_results,
    }

    if valid_results:
        scores = [r['score'] for r in valid_results]
        summary['average_score'] = sum(scores) / len(scores)
        summary['total_score'] = sum(scores)
        summary['min_score'] = min(scores)
        summary['max_score'] = max(scores)
    else:
        summary.update(
            {
                'average_score': 0.0,
                'total_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
            }
        )

    logger.info(
        f'Test evaluation completed: {len(valid_results)}/{len(test_results)} instances solved'
    )
    if valid_results:
        logger.info(f'Average speedup: {summary["average_score"]:.4f}x')

    logger.info(f'{"-" * 50} END Test Instance Evaluation {"-" * 50}')
    return summary


def process_training_and_testing(
    metadata: EvalMetadata,
    task_name: str,
    reset_logger: bool = True,
    enable_volumes: bool = True,
) -> EvalOutput:
    """Process training on validation cases and testing on remaining cases."""
    # Create unique workspace_id with timestamp to support multiple runs
    model_name = (
        metadata.llm_config.model.split('/')[-1].replace(':', '_').replace('@', '-')
    )
    agent_name = metadata.agent_class
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[
        :-3
    ]  # Include milliseconds for uniqueness
    workspace_id = f'{task_name}_{agent_name}_{model_name}_{timestamp}_experiment'

    config = get_config(metadata, workspace_id, enable_volumes)

    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, workspace_id, log_dir)

    else:
        logger.info(f'Starting training and testing for {task_name}.')

    # read from task_dir
    problem_statement = open(
        f'evaluation/benchmarks/algotune/tasks/{task_name}/problem_statement.txt'
    ).read()

    # Prepare instruction for training phase
    instruction = f"""You are tasked with developing and optimizing an algorithm.

  **Task Description:**
  {problem_statement}

  You should create Solver class and function solve() in `/workspace/solver.py` by yourself.

  The additional packages have been installed in this environment: /usr/local/bin/python.
"""

    # Create unique session ID for container isolation
    unique_sid = f'{workspace_id}_{os.getpid()}_{int(datetime.now().timestamp())}'

    runtime = create_runtime(config, sid=unique_sid)

    call_async_from_sync(runtime.connect)

    try:
        initialize_runtime(runtime, task_name)

        # Create partial function for user response
        user_response_fn = functools.partial(algotune_user_response, runtime=runtime)

        # Run the controller for training phase
        state: State | None = asyncio.run(
            run_controller(
                config=config,
                initial_user_action=MessageAction(content=instruction),
                runtime=runtime,
                fake_user_response_fn=user_response_fn,
            )
        )

        if state is None:
            raise ValueError('State should not be None.')

        # After training, evaluate on test cases
        test_results = evaluate_test_cases(runtime, task_name)

        metrics = state.metrics.get() if state.metrics else None
        histories = compatibility_for_eval_history_pairs(state.history)

        # Save the output
        output = EvalOutput(
            instance_id=workspace_id,
            instance={'task_name': task_name},
            instruction=instruction,
            metadata=metadata,
            history=histories,
            metrics=metrics,
            error=state.last_error if state and state.last_error else None,
            test_result={'result_summary': test_results},
        )
        return output
    finally:
        # Ensure runtime is properly closed to release resources
        try:
            runtime.close()
            logger.info(f'Runtime closed successfully for workspace: {workspace_id}')
        except Exception as e:
            logger.warning(f'Failed to close runtime for workspace {workspace_id}: {e}')


def process_task(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    """
    Wrapper function to process a single task, called by run_evaluation.
    """
    task_name = instance['task_name']
    enable_volumes = metadata.details.get('enable_volumes', False)
    return process_training_and_testing(
        metadata=metadata,
        task_name=task_name,
        reset_logger=reset_logger,
        enable_volumes=enable_volumes,
    )


if __name__ == '__main__':
    parser = get_evaluation_parser()
    available_tasks = discover_tasks()

    optim_task_choices = ['all'] + list(available_tasks.keys())
    parser.add_argument(
        '--optim_task',
        type=str,
        choices=optim_task_choices,
        default='all',
        help=f'Algorithm optimization task to run. Use "all" to run all tasks. Available: {optim_task_choices}',
    )
    parser.add_argument(
        '--enable_volumes',
        type=str,
        choices=['true', 'false'],
        default='false',
        help='Enable persistent volumes for the container to store workspace data. Default: false',
    )

    args, _ = parser.parse_known_args()

    if not available_tasks:
        logger.error('No valid tasks found in the algotune/tasks directory.')
        exit(1)

    # Determine which tasks to run
    if args.optim_task == 'all':
        tasks_to_run = list(available_tasks.keys())
        dataset_name = 'algotune_all'
    else:
        tasks_to_run = [args.optim_task]
        dataset_name = f'algotune_{args.optim_task}'

    # Create a DataFrame for the tasks
    tasks_df = pd.DataFrame({'instance_id': tasks_to_run, 'task_name': tasks_to_run})

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        llm_config.log_completions = True
        llm_config.modify_params = False
        llm_config.num_retries = 10

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    agent_config = (
        get_agent_config_arg(args.agent_config) if args.agent_config else None
    )

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    eval_output_dir_with_timestamp = os.path.join(
        args.eval_output_dir, 'algotune', timestamp
    )

    details = {'enable_volumes': args.enable_volumes.lower() == 'true'}

    metadata = make_metadata(
        llm_config,
        dataset_name,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        eval_output_dir_with_timestamp,
        agent_config=agent_config,
        details=details,
    )

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')

    # Filter out tasks that have already been completed
    instances_to_run = prepare_dataset(
        tasks_df,
        output_file,
        args.eval_n_limit,
    )

    # Use the evaluation utility to run the tasks
    run_evaluation(
        dataset=instances_to_run,
        metadata=metadata,
        output_file=output_file,
        num_workers=args.eval_num_workers,
        process_instance_func=process_task,
    )

    logger.info(f'Evaluation finished. Results are in {output_file}')
