import asyncio
import os

import pandas as pd
from datasets import load_dataset

from evaluation.utils.shared import (
    EvalMetadata,
    EvalOutput,
    codeact_user_response,
    compatibility_for_eval_history_pairs,
    get_default_sandbox_config_for_eval,
    make_metadata,
    prepare_dataset,
    reset_logger_for_multiprocessing,
    run_evaluation,
)
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
    get_llm_config_arg,
    get_parser,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import (
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have solved the question, please first send your answer to user through message and then exit.\n'
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'xingyaoww/od-eval-logic-reasoning:v1.0'
    sandbox_config.runtime_extra_deps = (
        '$OH_INTERPRETER_PATH -m pip install scitools-pyke'
    )

    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=sandbox_config,
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.enable_prompt_extensions = False
    return config


def get_choice(answer_str):
    choices = [
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'A)',
        'B)',
        'C)',
        'D)',
        'E)',
        'F)',
        'G)',
        'H)',
        'A.',
        'B.',
        'C.',
        'D.',
        'E.',
        'F.',
        'G.',
        'H.',
    ]
    for c in choices:
        if answer_str.startswith(c):
            return c.replace(')', '')

    if answer_str.startswith(':'):
        return answer_str.replace(':', '').replace('.', '').strip()
    return None


def get_test_result(
    model_answer: str,
    ground_truth: str,
) -> dict[str, bool]:
    gold_answer = ground_truth.replace('(', '').replace(')', '').strip()
    answer_str = model_answer if model_answer is not None else ''
    prediction = get_choice(answer_str)

    indicators = [
        'the correct option is',
        'the correct answer is',
        'The correct answer is',
        'The correct option is',
        'the answer is',
    ]
    if prediction is None:
        for indicator in indicators:
            if answer_str.find(indicator) >= 0:
                answer_str = answer_str.split(indicator)[1].strip()
                prediction = get_choice(answer_str)
                break

    isTrue = prediction == gold_answer
    test_result = {'result': isTrue}
    return test_result


CUR_EVAL_DIR = os.path.dirname(__file__)


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Initialization Fn {'-' * 50}")
    obs: CmdOutputObservation

    # Set instance id
    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command='cd /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    # copy logic_inference.py to /workspace
    runtime.copy_to(os.path.join(CUR_EVAL_DIR, 'logic_inference.py'), '/workspace')
    # check if the file exists
    obs = runtime.run_action(CmdRunAction(command='ls /workspace'))
    assert obs.exit_code == 0
    assert 'logic_inference.py' in obs.content

    runtime.add_env_vars({'DATASET_NAME': metadata.dataset})

    action = CmdRunAction(command='mkdir -p /workspace/.cache_program')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = IPythonRunCellAction(code='%pip install scitools-pyke')
    logger.info(action, extra={'msg_type': 'ACTION'})
    ipynb_obs = runtime.run_action(action)
    logger.info(ipynb_obs, extra={'msg_type': 'OBSERVATION'})

    logger.info(f"{'-' * 50} END Runtime Initialization Fn {'-' * 50}")


# Prepare instruction
with open(os.path.join(CUR_EVAL_DIR, 'instruction.txt'), 'r') as f:
    INSTRUCTION_TEMPLATE = f.read()


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    config = get_config(metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance['instance_id'], log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance["instance_id"]}.')

    instance_logic_programs = instance['raw_logic_programs'][0].strip()
    instruction = (
        INSTRUCTION_TEMPLATE.replace('[[dataset_name]]', dataset_name)
        .replace('[[logic_programs]]', instance_logic_programs)
        .replace('[[logic_inference_path.py]]', '/workspace/logic_inference.py')
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
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                metadata.agent_class
            ),
        )
    )
    # ======= Attempt to evaluate the agent's edits =======
    # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    final_message = ''
    for event in reversed(state.history):
        if isinstance(event, AgentFinishAction):
            final_message = event.thought
            break
        elif isinstance(event, MessageAction):
            final_message = event.content
            break

    final_message = final_message.strip("'")
    logger.info(
        f'Predicted answer: {final_message}, Ground truth: {instance["answer"]}'
    )

    test_result = get_test_result(
        model_answer=final_message, ground_truth=instance['answer']
    )
    test_result['final_message'] = final_message

    metrics = state.metrics.get() if state.metrics else None
    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=instance['instance_id'],
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result=test_result,
    )
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--dataset',
        type=str,
        help='the logic reasoning dataset to evaluate on {ProntoQA, ProofWriter}',
        default='ProofWriter',
    )
    parser.add_argument(
        '--data-split',
        type=str,
        help='data split to evaluate on {validation}',  # right now we only support validation split
        default='validation',
    )
    args, _ = parser.parse_known_args()

    dataset_name = args.dataset
    data_split = args.data_split
    dataset = load_dataset(f'renma/{dataset_name}')
    dataset_df = dataset[data_split].to_pandas()
    dataset_df.rename(columns={'id': 'instance_id'}, inplace=True)

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        dataset_name,
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
    )
    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    instances = prepare_dataset(dataset_df, output_file, args.eval_n_limit)
    run_evaluation(
        instances, metadata, output_file, args.eval_num_workers, process_instance
    )
