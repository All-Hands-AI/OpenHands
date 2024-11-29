import os
import tempfile
import time

import pandas as pd

from testgeneval.test_spec import TestGenEvalInstance, TestSpec, make_test_spec
from testgeneval.constants import MUTATION_TIMEOUT, TESTS_SUFFIX, COVERAGE_PREFIX
from testgeneval.utils import load_testgeneval_dataset
from testgeneval.pygments_utils import tokenize_code

from evaluation.swe_bench.run_infer import get_instance_docker_image
from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.core.config import (
    AppConfig,
    SandboxConfig,
    get_parser,
)

from testgeneval.metrics import (
    code_bleu,
    bleu,
    exact_match,
    edit_sim,
    rouge_l,
)

from report_utils import check_coverage, check_passed, check_mutation, count_methods, get_lines_of_code
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation

# TODO: migrate all swe-bench docker to ghcr.io/openhands
DOCKER_IMAGE_PREFIX = os.environ.get('EVAL_DOCKER_IMAGE_PREFIX', 'docker.io/kdjain/')
logger.info(f'Using docker image prefix: {DOCKER_IMAGE_PREFIX}')

def get_config(instance: pd.Series) -> AppConfig:
    # We use a different instance image for the each instance of swe-bench eval
    base_container_image = get_instance_docker_image(instance['instance_id'])
    logger.info(
        f'Using instance container image: {base_container_image}. '
        f'Please make sure this image exists. '
        f'Submit an issue on https://github.com/All-Hands-AI/OpenHands if you run into any issues.'
    )
    config = AppConfig(
        run_as_openhands=False,
        runtime=os.environ.get('RUNTIME', 'eventstream'),
        sandbox=SandboxConfig(
            base_container_image=base_container_image,
            use_host_network=False,
            # large enough timeout, since some testcases take very long to run
            timeout=1800,
            api_key=os.environ.get('ALLHANDS_API_KEY', None),
            remote_runtime_api_url=os.environ.get('SANDBOX_REMOTE_RUNTIME_API_URL'),
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    return config


def compute_lexical_metrics(pred_suite, gold_suite):
    pred_loc = get_lines_of_code(pred_suite)
    gold_loc = get_lines_of_code(gold_suite)
    pred_methods = count_methods(pred_suite)
    gold_methods = count_methods(gold_suite)

    preds = tokenize_code(pred_suite)
    golds = tokenize_code(gold_suite)

    code_bleu_met = code_bleu(preds, golds, "Python3")
    bleu_met = bleu(preds, golds)
    xmatch_met = exact_match(preds, golds)
    edit_sim_met = edit_sim(preds, golds)
    # cb_score = codebert_score(["".join(golds)], ["".join(preds)], pl)
    rouge_vals = rouge_l(golds, preds)
    rouge_f = rouge_vals["f"]
    rouge_p = rouge_vals["p"]
    rouge_r = rouge_vals["r"]
    return {
        "pred_loc": pred_loc,
        "gold_loc": gold_loc,
        "pred_methods": pred_methods,
        "gold_methods": gold_methods,
        "code_bleu": code_bleu_met, 
        "bleu": bleu_met, 
        "xmatch": xmatch_met, 
        "edit_sim": edit_sim_met, 
        "rouge_f": rouge_f, 
        "rouge_p": rouge_p, 
        "rouge_r": rouge_r
    }


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata | None = None,
    reset_logger: bool = True,
) -> EvalOutput:
    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        global output_file
        log_dir = output_file.replace('.jsonl', '.logs')
        os.makedirs(log_dir, exist_ok=True)
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    config = get_config(instance)
    instance_id = instance.instance_id
    test_suite = instance['test_suite']
    test_spec: TestSpec = instance['test_spec']
    logger.info(f'Starting evaluation for instance {instance_id}.')

    if 'test_result' not in instance.keys():
        instance['test_result'] = {}

    instance['test_result']['report'] = {
        'empty_generation': False,
        'coverage': 0,
        'mutation_score': 0,
        'mutation_error': 0,
        'error_eval': False,
        'test_pass': False,
        'test_timeout': False,
        'test_output': '',
        'coverage_output': '',
        'mutation_output': '',
    }

    instance['test_result']['lexical'] = {
        'pred_loc': 0,
        'gold_loc': 0,
        'pred_methods': 0,
        'gold_methods': 0,
        'bleu': 0,
        'code_bleu': 0,
        'xmatch': 0,
        'edit_sim': 0,
        'rouge_f': 0,
        'rouge_p': 0,
        'rouge_r': 0,
    }

    if test_suite == '':
        instance['test_result']['report']['empty_generation'] = True
        return EvalOutput(
            instance_id=instance_id,
            test_result=instance['test_result'],
        )

    if not args.skip_lexical:
        lexical_metrics = compute_lexical_metrics(test_suite, instance['instance']['test_suite'])
        instance['test_result']['lexical'] = lexical_metrics
    
    runtime = create_runtime(config)

    # Get patch and save it to /tmp/patch.diff
    with tempfile.TemporaryDirectory() as temp_dir:
        # Patch file
        test_suite_path = os.path.join(temp_dir, 'test_suite.py')
        with open(test_suite_path, 'w') as f:
            f.write(test_suite)
        runtime.copy_to(test_suite_path, '/tmp')

        # Test script
        test_script_path = os.path.join(temp_dir, 'test.sh')
        with open(test_script_path, 'w') as f:
            f.write(test_spec.test_script)
        runtime.copy_to(test_script_path, '/tmp')

           # Test script
        mutation_script_path = os.path.join(temp_dir, 'mutation.sh')
        with open(mutation_script_path, 'w') as f:
            f.write(test_spec.mutation_script)
        runtime.copy_to(mutation_script_path, '/tmp')

    # Set +x
    action = CmdRunAction(command='chmod +x /tmp/test.sh')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0


    action = CmdRunAction(command='chmod +x /tmp/mutation.sh')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command=f'cp /tmp/test_suite.py /testbed/{instance["test_file"]}')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    try:
        # Run eval script in background and save output to log file
        log_file = '/tmp/eval_output.log'
        action = CmdRunAction(
            command=f'/tmp/test.sh > {log_file} 2>&1 & echo $!', keep_prompt=False
        )
        action.timeout = 60  # Short timeout just to get the process ID
        obs = runtime.run_action(action)

        if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
            pid = obs.content.split()[-1].strip()
            logger.info(
                f'[{instance_id}] Evaluation process started with PID: {pid}'
            )

            # Poll for completion
            start_time = time.time()
            timeout = 1800  # 30 minutes
            while True:
                seconds_elapsed = time.time() - start_time
                if seconds_elapsed > timeout:
                    logger.info(
                        f'[{instance_id}] Evaluation timed out after {timeout} seconds'
                    )
                    instance['test_result']['report']['test_timeout'] = True
                    break
                check_action = CmdRunAction(
                    command=f'ps -p {pid} > /dev/null; echo $?', keep_prompt=False
                )
                check_action.timeout = 60
                check_obs = runtime.run_action(check_action)
                if (
                    isinstance(check_obs, CmdOutputObservation)
                    and check_obs.content.split()[-1].strip() == '1'
                ):
                    logger.info(
                        f'[{instance_id}] Evaluation process completed after {seconds_elapsed} seconds'
                    )
                    break
                logger.info(
                    f'[{instance_id}] [{seconds_elapsed:.0f}s] Evaluation still running, waiting...'
                )
                time.sleep(30)  # Wait for 30 seconds before checking again

            # Read the log file
            test_action = CmdRunAction(command=f'cat {log_file}', keep_prompt=False)
            test_action.timeout = 300
            test_obs = runtime.run_action(test_action)

            # Grade answer
            if isinstance(test_obs, CmdOutputObservation) and test_obs.exit_code == 0:
                test_output = test_obs.content
                assert isinstance(test_output, str)
                unit_test_output, coverage_output, mutation_output = '', '', ''

                if TESTS_SUFFIX in test_output:
                    unit_test_output = test_output.split(TESTS_SUFFIX)[0]
                    instance['test_result']['test_output'] = unit_test_output
                
                if COVERAGE_PREFIX in test_output:
                    coverage_output = test_output.split(COVERAGE_PREFIX)[1]
                    instance['test_result']['report']['coverage_output'] = coverage_output

                # Get report from test output
                logger.info(f'[{instance_id}] Grading answer...')

                passed = check_passed(unit_test_output)
                coverage = check_coverage(coverage_output)
        else:
            logger.info(f'[{instance_id}] Error when starting eval:\n{obs.content}')
            instance['test_result']['report']['error_eval'] = True

        return EvalOutput(
            instance_id=instance_id,
            test_result=instance['test_result'],
        )
    finally:
        runtime.close()


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--input-file',
        type=str,
        help='Path to input predictions file',
        required=True,
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='kjain14/testgeneval',
        help='data set to evaluate on, either full-test or lite-test',
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        help='split to evaluate on',
    )
    parser.add_argument(
        '--skip_mutation',
        action='store_true',
        help='timeout for running mutation testing',
    )
    parser.add_argument(
        '--skip_lexical',
        action='store_true',
        help='timeout for running mutation testing',
    )
    parser.add_argument(
        '--mutation_timeout',
        type=str,
        default=MUTATION_TIMEOUT,
        help='timeout for running mutation testing',
    )
    args, _ = parser.parse_known_args()

    # Load SWE-Bench dataset
    full_dataset: list[TestGenEvalInstance] = load_testgeneval_dataset(
        args.dataset, args.split
    )
    id_to_instance = {
        instance['id']: instance for instance in full_dataset
    }
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
        and 'test_suite' in predictions['test_result'].iloc[0]
    ):
        raise ValueError(
            'Input file must contain test_suite column OR test_result column with test_suite field.'
        )
    assert len(predictions['id'].unique()) == len(
        predictions
    ), 'id column must be unique.'

    if 'test_suite' not in predictions.columns:
        predictions['test_suite'] = predictions['test_result'].apply(
            lambda x: x['test_suite']
        )
    assert {'id', 'test_suite'}.issubset(
        set(predictions.columns)
    ), 'Input file must contain id and test_suite columns.'

    # Merge predictions with dataset
    predictions['instance'] = predictions['id'].apply(
        lambda x: id_to_instance[x]
    )
    predictions['test_spec'] = predictions['instance'].apply(lambda x: make_test_spec(x, args.mutation_timeout))

    # Prepare dataset
    output_file = args.input_file.replace('.jsonl', '.swebench_eval.jsonl')
    instances = prepare_dataset(predictions, output_file, args.eval_n_limit)

    run_evaluation(
        instances,
        metadata=None,
        output_file=output_file,
        num_workers=args.eval_num_workers,
        process_instance_func=process_instance,
    )

    # Load evaluated predictions & print number of resolved predictions
    evaluated_predictions = pd.read_json(output_file, lines=True)
    fields = ['resolved', 'failed_apply_patch', 'error_eval', 'empty_generation']

    def count_report_field(row, field):
        return row['test_result']['report'][field]

    for field in fields:
        count = evaluated_predictions.apply(
            count_report_field, args=(field,), axis=1
        ).sum()
        logger.info(
            f'# {field}: {count} / {len(evaluated_predictions)}. ({count / len(evaluated_predictions):.2%})'
        )
