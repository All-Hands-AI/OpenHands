import os
import tempfile
import time
from functools import partial

import pandas as pd
from report_utils import (
    check_coverage,
    check_mutation,
    count_methods,
    get_lines_of_code,
)

from evaluation.benchmarks.testgeneval.compute_readability import compute_readability
from evaluation.benchmarks.testgeneval.constants import (
    COVERAGE_PREFIX,
    MUTATION_BUFFER,
    MUTATION_TEMPLATE,
    MUTATION_TIMEOUT,
    TESTS_FAILED,
    TESTS_SUFFIX,
)
from evaluation.benchmarks.testgeneval.metrics import (
    bleu,
    code_bleu,
    edit_sim,
    exact_match,
    rouge_l,
)
from evaluation.benchmarks.testgeneval.pygments_utils import tokenize_code
from evaluation.benchmarks.testgeneval.run_infer import get_instance_docker_image
from evaluation.benchmarks.testgeneval.test_spec import (
    TestGenEvalInstance,
    TestSpec,
    make_test_spec,
)
from evaluation.benchmarks.testgeneval.utils import (
    load_testgeneval_dataset,
)
from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.core.config import AppConfig, SandboxConfig, get_parser
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.utils.async_utils import call_async_from_sync

DOCKER_IMAGE_PREFIX = os.environ.get('EVAL_DOCKER_IMAGE_PREFIX', 'docker.io/kdjain/')
logger.info(f'Using docker image prefix: {DOCKER_IMAGE_PREFIX}')


def get_config(instance: pd.Series) -> AppConfig:
    base_container_image = get_instance_docker_image(instance['instance_id'])
    assert (
        base_container_image
    ), f"Invalid container image for instance {instance['instance_id']}."
    logger.info(f'Using instance container image: {base_container_image}.')
    return AppConfig(
        run_as_openhands=False,
        runtime=os.environ.get('RUNTIME', 'eventstream'),
        sandbox=SandboxConfig(
            base_container_image=base_container_image,
            use_host_network=False,
            timeout=1800,
            api_key=os.environ.get('ALLHANDS_API_KEY'),
            remote_runtime_api_url=os.environ.get('SANDBOX_REMOTE_RUNTIME_API_URL'),
        ),
        workspace_base=None,
        workspace_mount_path=None,
    )


def compute_lexical_metrics(pred_suite, gold_suite):
    pred_loc = get_lines_of_code(pred_suite)
    gold_loc = get_lines_of_code(gold_suite)
    pred_methods = count_methods(pred_suite)
    gold_methods = count_methods(gold_suite)
    readability_pred = compute_readability(pred_suite)
    readability_gold = compute_readability(gold_suite)

    preds = tokenize_code(pred_suite)
    golds = tokenize_code(gold_suite)

    return {
        'pred_loc': pred_loc,
        'gold_loc': gold_loc,
        'pred_readability': readability_pred,
        'gold_readability': readability_gold,
        'pred_methods': pred_methods,
        'gold_methods': gold_methods,
        'code_bleu': code_bleu(preds, golds, 'Python3'),
        'bleu': bleu(preds, golds),
        'xmatch': exact_match(preds, golds),
        'edit_sim': edit_sim(preds, golds),
        'rouge_f': rouge_l(golds, preds)['f'],
        'rouge_p': rouge_l(golds, preds)['p'],
        'rouge_r': rouge_l(golds, preds)['r'],
    }


def run_command(runtime, command, timeout=600):
    action = CmdRunAction(command=command)
    action.timeout = timeout
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    return obs


def run_tests(runtime, instance, test_script, log_file='/tmp/test_output.log'):
    action = CmdRunAction(
        command=f'bash {test_script} > {log_file} 2>&1 & echo $!', keep_prompt=False
    )
    action.timeout = 60
    obs = runtime.run_action(action)

    assert isinstance(obs, CmdOutputObservation), 'Failed to start test script.'
    pid = obs.content.split()[-1].strip()
    logger.info(f'[{instance.id}] Test process started with PID: {pid}')

    start_time = time.time()
    timeout = 1800
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            logger.info(f'[{instance.id}] Test process timed out.')
            instance['test_result']['report']['test_timeout'] = True
            break

        check_action = CmdRunAction(
            command=f'ps -p {pid} > /dev/null; echo $?', keep_prompt=False
        )
        check_obs = runtime.run_action(check_action)
        if (
            isinstance(check_obs, CmdOutputObservation)
            and check_obs.content.split()[-1].strip() == '1'
        ):
            logger.info(f'[{instance.id}] Test process completed.')
            break
        time.sleep(30)

    test_action = CmdRunAction(command=f'cat {log_file}', keep_prompt=False)
    test_action.timeout = 300
    test_obs = runtime.run_action(test_action)
    assert isinstance(test_obs, CmdOutputObservation), 'Failed to retrieve test output.'
    return test_obs.exit_code, test_obs.content, elapsed_time


def run_mutation_testing(
    runtime, instance, mutation_script, log_file='/tmp/mutation_output.log'
):
    action = CmdRunAction(
        command=f'bash {mutation_script} > {log_file} 2>&1 & echo $!', keep_prompt=False
    )
    action.timeout = 60
    obs = runtime.run_action(action)

    assert isinstance(obs, CmdOutputObservation), 'Failed to start test script.'
    pid = obs.content.split()[-1].strip()
    logger.info(f'[{instance.id}] Mutation process started with PID: {pid}')

    start_time = time.time()
    timeout = 4000
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            logger.info(f'[{instance.id}] Mutation process timed out.')
            instance['test_result']['report']['mutation_timeout'] = True
            break

        check_action = CmdRunAction(
            command=f'ps -p {pid} > /dev/null; echo $?', keep_prompt=False
        )
        check_obs = runtime.run_action(check_action)
        if (
            isinstance(check_obs, CmdOutputObservation)
            and check_obs.content.split()[-1].strip() == '1'
        ):
            logger.info(f'[{instance.id}] Mutation process completed.')
            break
        time.sleep(30)

    assert isinstance(obs, CmdOutputObservation), 'Failed to run mutation script.'
    mutation_action = CmdRunAction(command=f'cat {log_file}', keep_prompt=False)
    mutation_action.timeout = 300
    mutation_obs = runtime.run_action(mutation_action)
    assert isinstance(
        mutation_obs, CmdOutputObservation
    ), 'Failed to retrieve mutation output.'
    return mutation_obs.exit_code, mutation_obs.content


def grade_test_output(test_output: str, test_spec: TestSpec):
    unit_test_output, coverage_output = '', ''
    if TESTS_SUFFIX in test_output:
        unit_test_output = test_output.split(TESTS_SUFFIX)[0]
    if COVERAGE_PREFIX in test_output:
        coverage_output = test_output.split(COVERAGE_PREFIX)[1]
    coverage_success, coverage = check_coverage(coverage_output, test_spec.code_file)
    return coverage_success, coverage, unit_test_output, coverage_output


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
    log_dir: str | None = None,
) -> EvalOutput:
    """
    Evaluate agent performance on a TestGenEval problem instance.

    Note that this signature differs from the expected input to `run_evaluation`. Use
    `functools.partial` to provide optional arguments before passing to the evaluation harness.

    Args:
        log_dir (str | None, default=None): Path to directory where log files will be written. Must
        be provided if `reset_logger` is set.

    Raises:
        AssertionError: if the `reset_logger` flag is set without a provided log directory.
    """
    if reset_logger:
        assert (
            log_dir is not None
        ), "Can't reset logger without a provided log directory."
        os.makedirs(log_dir, exist_ok=True)
        reset_logger_for_multiprocessing(logger, instance.id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.id}.')

    config = get_config(instance)
    id = instance.id
    logger.info(f'Starting evaluation for instance {id}.')

    instance['test_result']['report'] = {
        'test_output': '',
        'coverage_output': '',
        'mutation_output': '',
        'empty_generation': False,
        'error_eval': False,
        'test_pass': False,
        'test_timeout': False,
        'mutation_timeout': False,
        'coverage_success': False,
        'mutation_success': False,
        'coverage': 0,
        'mutation_score': 0,
        'mutation_error_interval': -1,
        'num_mutants': -1,
    }

    instance['test_result']['lexical'] = {
        'pred_loc': -1,
        'gold_loc': -1,
        'pred_readability': -1,
        'gold_readability': -1,
        'pred_methods': -1,
        'gold_methods': -1,
        'code_bleu': -1,
        'bleu': -1,
        'xmatch': -1,
        'edit_sim': -1,
        'rouge_f': -1,
        'rouge_p': -1,
        'rouge_r': -1,
    }

    if instance['test_suite'] == '' or instance['test_suite'] is None:
        instance['test_result']['report']['empty_generation'] = True
        return EvalOutput(
            instance_id=instance.instance_id, test_result=instance['test_result']
        )

    if not args.skip_lexical:
        lexical_metrics = compute_lexical_metrics(
            instance['test_suite'], instance['instance']['test_src']
        )
        instance['test_result']['lexical'] = lexical_metrics

    test_suite = instance['test_suite']
    test_spec: TestSpec = instance['test_spec']
    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    with tempfile.TemporaryDirectory() as temp_dir:
        test_suite_path = os.path.join(temp_dir, 'test_suite.py')
        with open(test_suite_path, 'w') as f:
            f.write(test_suite)
        runtime.copy_to(test_suite_path, '/tmp')

        test_script_path = os.path.join(temp_dir, 'test.sh')
        with open(test_script_path, 'w') as f:
            f.write(test_spec.test_script)
        runtime.copy_to(test_script_path, '/tmp')

        mutation_script_path = os.path.join(temp_dir, 'mutation.sh')
        with open(mutation_script_path, 'w') as f:
            f.write(test_spec.mutation_script)
        runtime.copy_to(mutation_script_path, '/tmp')

    try:
        run_command(runtime, 'chmod +x /tmp/test.sh /tmp/mutation.sh')
        run_command(runtime, f'cp /tmp/test_suite.py /testbed/{test_spec.test_file}')

        _, test_output, test_time = run_tests(runtime, instance, '/tmp/test.sh')
        instance['test_result']['report']['test_output'] = test_output
        if TESTS_FAILED not in test_output:
            coverage_success, coverage, unit_test_output, coverage_output = (
                grade_test_output(test_output, test_spec)
            )
            instance['test_result']['report'].update(
                {
                    'test_output': unit_test_output,
                    'coverage_output': coverage_output,
                    'test_pass': True,
                    'coverage_success': coverage_success,
                    'coverage': coverage if coverage_success else 0,
                }
            )

            if not args.skip_mutation and coverage_success:
                mutation_timeout = max(10, 1.5 * test_time)
                mutation_toml = MUTATION_TEMPLATE.format(
                    test_cmd=test_spec.test_cmd,
                    source_fp=test_spec.code_file,
                    timeout=mutation_timeout,
                )

                with tempfile.TemporaryDirectory() as temp_dir:
                    mutation_toml_path = os.path.join(temp_dir, 'mutation.toml')
                    with open(mutation_toml_path, 'w') as f:
                        f.write(mutation_toml)
                    runtime.copy_to(mutation_toml_path, '/tmp')

                run_command(runtime, 'cp /tmp/mutation.toml /testbed/mutation.toml')

                mutation_code, mutation_output = run_mutation_testing(
                    runtime, instance, '/tmp/mutation.sh'
                )
                instance['test_result']['report']['mutation_output'] = mutation_output
                if mutation_output and mutation_code == 0:
                    (
                        mutation_success,
                        num_mutants,
                        mutation_score,
                        mutation_confidence_interval,
                    ) = check_mutation(mutation_output)
                    instance['test_result']['report']['num_mutants'] = num_mutants
                    instance['test_result']['report']['mutation_success'] = (
                        mutation_success
                    )
                    instance['test_result']['report']['mutation_score'] = mutation_score
                    instance['test_result']['report']['mutation_error_interval'] = (
                        mutation_confidence_interval
                    )

        return EvalOutput(
            instance_id=instance.instance_id, test_result=instance['test_result']
        )
    except Exception as e:
        logger.error(f'Error processing instance {instance.id}: {e}')
        raise RuntimeError(
            instance.id,
            'Unexpected output...',
            logger,
        )

    finally:
        runtime.close()


def count_and_log_fields(evaluated_predictions, fields, key):
    """
    Count and log the sum of specified fields in the evaluated predictions,
    ignoring fields with a value of -1. If all values for a field are -1,
    return -1.

    :param evaluated_predictions: DataFrame containing evaluation results
    :param fields: List of field names to count
    :param key: Key to access the field values ('report' or 'lexical')
    """

    def count_field(row, field):
        value = row['test_result'][key][field]
        return (
            value if value != -1 else None
        )  # Ignore -1 fields by treating them as None

    for field in fields:
        # Extract the valid values for the field, ignoring -1
        valid_values = evaluated_predictions.apply(
            count_field, args=(field,), axis=1
        ).dropna()

        if valid_values.empty:  # If all values are -1
            logger.info(f'# {field}: -1 (All values are -1)')
        else:
            count = valid_values.sum()  # Sum of valid values
            length = len(valid_values)  # Count of valid entries
            logger.info(f'# {field}: {length}. ({count / length:.2f})')


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--input-file', type=str, required=True, help='Path to input predictions file'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='kjain14/testgeneval',
        help='Dataset to evaluate on',
    )
    parser.add_argument(
        '--split', type=str, default='test', help='Split to evaluate on'
    )
    parser.add_argument(
        '--skip_mutation', action='store_true', help='Skip mutation testing'
    )
    parser.add_argument(
        '--skip_lexical', action='store_true', help='Skip lexical metrics'
    )
    parser.add_argument(
        '--mutation_timeout',
        type=int,
        default=MUTATION_TIMEOUT,
        help='Mutation timeout',
    )
    parser.add_argument(
        '--mutation_buffer',
        type=int,
        default=MUTATION_BUFFER,
        help='Mutation buffer',
    )
    args, _ = parser.parse_known_args()

    dataset: list[TestGenEvalInstance] = load_testgeneval_dataset(
        args.dataset, args.split
    )

    logger.info(
        f'Loaded dataset {args.dataset} with split {args.split} to run inference on.'
    )

    # Load predictions
    assert args.input_file.endswith('.jsonl'), 'Input file must be a jsonl file.'
    predictions = pd.read_json(args.input_file, lines=True)
    assert (
        'instance_id' in predictions.columns
    ), 'Input file must contain instance_id column.'

    if 'test_suite' not in predictions.columns and (
        'test_result' in predictions.columns
        and 'test_suite' in predictions['test_result'].iloc(0)
    ):
        raise ValueError(
            'Input file must contain test_suite column OR test_result column with test_suite field.'
        )

    if 'id' not in predictions.columns and ('id' in predictions['instance'].iloc(0)):
        raise ValueError(
            'Input file must contain id column OR instance column with id field.'
        )

    if 'id' not in predictions.columns:
        predictions['id'] = predictions['instance'].apply(lambda x: x['id'])

    if 'instance_id' not in predictions.columns and (
        'instance_id' in predictions['instance'].iloc(0)
    ):
        raise ValueError(
            'Input file must contain id column OR instance column with id field.'
        )

    if 'instance_id' not in predictions.columns:
        predictions['instance_id'] = predictions['instance'].apply(
            lambda x: x['instance_id']
        )

    if 'test_suite' not in predictions.columns:
        predictions['test_suite'] = predictions['test_result'].apply(
            lambda x: x['test_suite']
        )

    assert len(predictions['id'].unique()) == len(
        predictions
    ), 'id column must be unique.'

    assert len(predictions['instance_id'].unique()) == len(
        predictions
    ), 'instance_id column must be unique.'

    assert {'id', 'test_suite', 'instance_id'}.issubset(
        set(predictions.columns)
    ), 'Input file must contain id, instance_id and test_suite columns.'

    predictions['test_spec'] = predictions['instance'].apply(
        lambda x: make_test_spec(x, args.mutation_timeout, args.mutation_buffer)
    )

    output_file = args.input_file.replace('.jsonl', '.testgeneval.jsonl')
    instances = prepare_dataset(predictions, output_file, args.eval_n_limit)

    # If possible, load the relevant metadata to avoid issues with `run_evaluation`.
    metadata: EvalMetadata | None = None
    metadata_filepath = os.path.join(os.path.dirname(args.input_file), 'metadata.json')
    if os.path.exists(metadata_filepath):
        with open(metadata_filepath, 'r') as metadata_file:
            data = metadata_file.read()
            metadata = EvalMetadata.model_validate_json(data)

    # The evaluation harness constrains the signature of `process_instance_func` but we need to
    # pass extra information. Build a new function object to avoid issues with multiprocessing.
    process_instance_func = partial(
        process_instance, log_dir=output_file.replace('.jsonl', '.logs')
    )

    run_evaluation(
        instances,
        metadata=None,
        output_file=output_file,
        num_workers=args.eval_num_workers,
        process_instance_func=process_instance_func,
    )

    # Load evaluated predictions & print number of resolved predictions
    evaluated_predictions = pd.read_json(output_file, lines=True)
    report_fields = [
        'coverage',
        'mutation_score',
        'test_pass',
        'empty_generation',
        'coverage_success',
        'test_timeout',
        'error_eval',
    ]
    lexical_fields = [
        'pred_loc',
        'gold_loc',
        'pred_methods',
        'gold_methods',
        'code_bleu',
        'bleu',
        'xmatch',
        'edit_sim',
        'rouge_f',
        'rouge_p',
        'rouge_r',
    ]

    # Log report and lexical fields
    count_and_log_fields(evaluated_predictions, report_fields, key='report')
    count_and_log_fields(evaluated_predictions, lexical_fields, key='lexical')
