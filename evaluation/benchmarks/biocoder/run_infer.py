import asyncio
import functools
import json
import os
import tempfile
from typing import Any

import pandas as pd
from datasets import load_dataset

from evaluation.benchmarks.biocoder.utils import BiocoderData
from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    codeact_user_response,
    compatibility_for_eval_history_pairs,
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
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': functools.partial(
        codeact_user_response, encapsulate_solution=True, try_parse=None
    ),
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please finish the interaction using the "finish" tool.\n'
}

FILE_EXT_MAP = {
    'python': 'py',
    'java': 'java',
    'c': 'c',
    'cpp': 'cpp',
    'javascript': 'js',
    'typescript': 'ts',
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    BIOCODER_BENCH_CONTAINER_IMAGE = 'public.ecr.aws/i5g0m1f6/eval_biocoder:v1.0'

    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=SandboxConfig(
            base_container_image=BIOCODER_BENCH_CONTAINER_IMAGE,
            enable_auto_lint=True,
            use_host_network=False,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.use_microagents = False
    return config


def initialize_runtime(
    runtime: Runtime,
    instance: BiocoderData,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Initialization Fn {'-' * 50}")
    obs: CmdOutputObservation

    file_ext = FILE_EXT_MAP[instance.language.lower()]

    action = CmdRunAction(command='mkdir -p /workspace && mkdir -p /testing_files')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    with tempfile.TemporaryDirectory() as tmpdir:
        context_path = os.path.join(tmpdir, 'context.' + file_ext)
        with open(context_path, 'w') as f:
            f.write(instance.contextCode)
        runtime.copy_to(context_path, '/testing_files')

        golden_path = os.path.join(tmpdir, 'golden.' + file_ext)
        with open(golden_path, 'w') as f:
            f.write(instance.goldenCode)
        runtime.copy_to(golden_path, '/testing_files')

        testcase_json = {
            'test_case_id': instance.test_case_id,
            'num_cases': 1000,
            'language': instance.language.lower(),
        }
        testcase_path = os.path.join(tmpdir, 'testcase_biocoder.json')
        with open(testcase_path, 'w') as f:
            f.write(json.dumps(testcase_json, indent=4))

        runtime.copy_to(testcase_path, '/testing_files')

    # setup paths
    remove_code_script = os.path.join(
        os.path.dirname(__file__), 'scripts', 'setup', 'remove_code.py'
    )
    runtime.copy_to(remove_code_script, '/testing_files')

    action = CmdRunAction(command='cd /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    # download repository archive
    repository_url = f"https://biocoder.lilbillbiscuit.com/repos/{instance.repository.split('/')[1]}.zip"
    action = CmdRunAction(command='wget -O repo.zip ' + repository_url)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0, f'Failed to download the repository: {obs.content}'

    # unzip the repository
    action = CmdRunAction(command='unzip -o -q repo.zip && rm repo.zip')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0, f'Failed to unzip the repository: {obs.content}'

    # chmod 777
    action = CmdRunAction(command='chmod -R 777 /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0, f'Failed to chmod the files: {obs.content}'

    # remove code for evaluation instance
    target_filepath = os.path.join(
        '/workspace', instance.repository.split('/')[1], instance.filePath
    )
    line_start = instance.lineStart
    line_end = instance.lineEnd
    language = instance.language.lower()
    action = CmdRunAction(
        command=f'python3 /testing_files/remove_code.py --target_filepath {target_filepath} --line_start {line_start} --line_end {line_end} --language {language}'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0, f'Failed to remove the code: {obs.content}'

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

    test_result = {'result': {}, 'metadata': {}}

    copy_changed_code_script = os.path.join(
        os.path.dirname(__file__), 'scripts', 'setup', 'copy_changed_code.py'
    )
    runtime.copy_to(copy_changed_code_script, '/testing_files')

    file_ext = FILE_EXT_MAP[instance.language.lower()]
    target_filepath = os.path.join(
        '/workspace', instance.repository.split('/')[1], instance.filePath
    )
    generated_path = os.path.join('/testing_files', 'generated.' + file_ext)

    action = CmdRunAction(
        command=f'python3 /testing_files/copy_changed_code.py --target_filepath {target_filepath} --generated_code_filepath {generated_path} --line_start {instance.lineStart} --include_signature'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    if obs.exit_code == 0:
        test_result['metadata']['1_copy_change_success'] = True

        action = CmdRunAction(command=f'cat {generated_path}')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        assert obs.exit_code == 0

        code = obs.content
        test_result['metadata']['1_copy_change_code'] = code
    else:
        test_result['metadata']['1_copy_change_success'] = False
        test_result['metadata']['1_copy_change_code'] = None

    action = CmdRunAction(command='cd /testing_files')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(
        command='/home/openhands/mambaforge/bin/mamba run -n test python3 /testing/start_test_openhands.py'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command='cat /testing_files/results_biocoder.json')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    if obs.exit_code == 0:
        test_result['metadata']['2_run_test_success'] = True
        test_result['metadata']['2_run_test_result'] = str(obs.content)
        json_obj = json.loads(obs.content)
        test_result['result'] = json_obj['result']
    else:
        test_result['metadata']['2_run_test_success'] = False
        test_result['metadata']['2_run_test_result'] = str(obs.content)

    logger.info(f"{'-' * 50} END Runtime Completion Fn {'-' * 50}")
    return test_result


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(metadata)
    instance = BiocoderData(**instance)
    print(instance)
    instance_id = f'{instance.repository}__{instance.instance_id[:10]}'

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance_id}.')

    # Prepare instruction
    instruction = (
        f'Please complete the function "{instance.signature}" in the file /workspace/{instance.repository.split("/")[1]}/{instance.filePath}.\n'
        f'The environment has been set up for you to start working. You may assume all necessary tools are installed.\n'
        f'To complete the task, you must directly modify the file and fill in the function, keeping in mind that the function signature is on line {instance.lineStart-1}\n\n'
        f'The function should do the following:\n'
        f'{instance.promptSummaryOnly}\n\n'
    )

    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        'You should NOT modify any other files other than the file intended. This means that you should NOT write any test cases.\n'
        'You may need context from other files in the repository to complete this task.'
        'Do NOT add any import statements or change anything else other than the writing the function body.\n'
        'You do not need to run the code to check if it works. \n'
        'Make sure to include proper formatting in Java and Python, including correct braces and/or indentation.\n'
    )
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[metadata.agent_class]

    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    initialize_runtime(runtime, instance)

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

    if state is None:
        raise ValueError('State should not be None.')

    test_result = complete_runtime(runtime, instance)
    metrics = state.metrics.get() if state.metrics else None
    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    test_result['generated'] = test_result['metadata']['1_copy_change_code']

    # Save the output
    output = EvalOutput(
        instance_id=instance.instance_id,
        instance=instance.to_dict(),
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result=test_result,
    )
    return output


if __name__ == '__main__':
    args = parse_arguments()

    dataset = load_dataset('lilbillbiscuit/biocoder_public')
    biocoder_tests = dataset['train'].to_pandas()
    biocoder_tests['instance_id'] = biocoder_tests['test_case_id']

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'biocoder',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(biocoder_tests, output_file, args.eval_n_limit)

    run_evaluation(
        instances, metadata, output_file, args.eval_num_workers, process_instance
    )
