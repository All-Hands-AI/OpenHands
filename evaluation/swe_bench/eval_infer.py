import os
import tempfile
from typing import Any

import pandas as pd
from pydantic import BaseModel
from swebench.harness.grading import get_eval_report
from swebench.harness.run_evaluation import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
)
from swebench.harness.test_spec import SWEbenchInstance, TestSpec, make_test_spec
from swebench.harness.utils import load_swebench_dataset

from evaluation.swe_bench.run_infer import get_instance_docker_image
from evaluation.utils.shared import (
    EvalOutput,
    prepare_dataset,
    run_evaluation,
)
from openhands.core.config import (
    AppConfig,
    SandboxConfig,
    get_parser,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation

# TODO: migrate all swe-bench docker to ghcr.io/openhands
DOCKER_IMAGE_PREFIX = os.environ.get('EVAL_DOCKER_IMAGE_PREFIX', 'docker.io/xingyaoww/')
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
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    return config


class SWEBenchEvalResult(BaseModel):
    instance_id: str
    apply_patch_output: str
    test_output: str
    resolved: bool
    ...


def process_instance(
    instance: pd.Series,
    *args: Any,  # args for run_evaluation
    **kwargs: Any,  # kwargs for run_evaluation
) -> EvalOutput:
    config = get_config(instance)
    instance_id = instance.instance_id
    model_patch = instance['model_patch']
    test_spec: TestSpec = instance['test_spec']
    logger.info(f'Starting evaluation for instance {instance_id}.')

    if 'test_result' not in instance.keys():
        instance['test_result'] = {}
    instance['test_result']['report'] = {
        'empty_generation': False,
        'resolved': False,
        'failed_apply_patch': False,
        'error_eval': False,
    }

    if model_patch == '':
        instance['test_result']['report']['empty_generation'] = True
        return EvalOutput(
            instance_id=instance_id,
            test_result=instance['test_result'],
        )

    runtime = create_runtime(config, sid=instance_id)

    # Get patch and save it to /tmp/patch.diff
    with tempfile.TemporaryDirectory() as temp_dir:
        # Patch file
        patch_file_path = os.path.join(temp_dir, 'patch.diff')
        with open(patch_file_path, 'w') as f:
            f.write(model_patch)
        runtime.copy_to(patch_file_path, '/tmp/patch.diff')
        # Eval script
        eval_script_path = os.path.join(temp_dir, 'eval.sh')
        with open(eval_script_path, 'w') as f:
            f.write(test_spec.eval_script)
        runtime.copy_to(eval_script_path, '/tmp/eval.sh')

    # Set +x
    action = CmdRunAction(command='chmod +x /tmp/eval.sh')
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Apply patch
    exec_command = (
        'cd /testbed && '
        "(git apply -v /tmp/patch.diff && echo 'APPLY_PATCH_PASS' || "
        "(echo 'Failed to apply patch with git apply, trying with patch command...' && "
        "(patch --batch --fuzz=5 -p1 -i /tmp/patch.diff && echo 'APPLY_PATCH_PASS' || "
        "echo 'APPLY_PATCH_FAIL'))"
    )
    action = CmdRunAction(command=exec_command)
    action.timeout = 600
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, CmdOutputObservation)
    apply_patch_output = obs.content
    assert isinstance(apply_patch_output, str)

    try:
        if 'APPLY_PATCH_FAIL' in apply_patch_output:
            logger.info(f'[{instance_id}] {APPLY_PATCH_FAIL}:\n{apply_patch_output}')
            instance['test_result']['report']['failed_apply_patch'] = True

            return EvalOutput(
                instance_id=instance_id,
                test_result=instance['test_result'],
            )
        elif 'APPLY_PATCH_PASS' in apply_patch_output:
            logger.info(f'[{instance_id}] {APPLY_PATCH_PASS}:\n{apply_patch_output}')
            # Execution for eval
            action = CmdRunAction(command='/tmp/eval.sh', keep_prompt=False)
            action.timeout = 1800
            logger.info(action, extra={'msg_type': 'ACTION'})
            obs = runtime.run_action(action)
            logger.info(obs, extra={'msg_type': 'OBSERVATION'})
            if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
                test_output = obs.content
                assert isinstance(test_output, str)

                # Get report from test output
                logger.info(f'[{instance_id}] Grading answer...')
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_output_path = os.path.join(temp_dir, 'test_output.txt')
                    with open(test_output_path, 'w') as f:
                        f.write(test_output)
                    _report = get_eval_report(
                        test_spec=test_spec,
                        prediction=model_patch,
                        log_path=test_output_path,
                        include_tests_status=True,
                    )
                    report = _report[instance_id]
                    logger.info(
                        f"[{instance_id}] report: {report}\nResult for {instance_id}: resolved: {report['resolved']}"
                    )
                    instance['test_result']['report']['resolved'] = report['resolved']
            else:
                logger.info(f'[{instance_id}] Error when running eval:\n{obs.content}')
                instance['test_result']['report']['error_eval'] = True

            return EvalOutput(
                instance_id=instance_id,
                test_result=instance['test_result'],
            )
        else:
            logger.info(
                f'[{instance_id}] Unexpected output when applying patch:\n{apply_patch_output}'
            )
            raise RuntimeError(
                instance_id,
                f'Unexpected output when applying patch:\n{apply_patch_output}',
                logger,
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

    # Load SWE-Bench dataset
    full_dataset: list[SWEbenchInstance] = load_swebench_dataset(
        args.dataset, args.split
    )
    instance_id_to_instance = {
        instance['instance_id']: instance for instance in full_dataset
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

    if 'model_patch' not in predictions.columns and (
        'test_result' in predictions.columns
        and 'model_patch' in predictions['test_result'].iloc[0]
    ):
        raise ValueError(
            'Input file must contain model_patch column OR test_result column with model_patch field.'
        )
    assert len(predictions['instance_id'].unique()) == len(
        predictions
    ), 'instance_id column must be unique.'

    if 'model_patch' not in predictions.columns:
        predictions['model_patch'] = predictions['test_result'].apply(
            lambda x: x['git_patch']
        )
    assert {'instance_id', 'model_patch'}.issubset(
        set(predictions.columns)
    ), 'Input file must contain instance_id and model_patch columns.'

    # Merge predictions with dataset
    predictions['instance'] = predictions['instance_id'].apply(
        lambda x: instance_id_to_instance[x]
    )
    predictions['test_spec'] = predictions['instance'].apply(make_test_spec)

    # Prepare dataset
    output_file = args.input_file.replace('.jsonl', '.swebench_evaled.jsonl')
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
