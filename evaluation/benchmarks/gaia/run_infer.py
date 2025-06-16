import asyncio
import copy
import functools
import os
import re

import huggingface_hub
import pandas as pd
from datasets import load_dataset
from pydantic import SecretStr

from evaluation.benchmarks.gaia.scorer import question_scorer
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
    OpenHandsConfig,
    get_llm_config_arg,
    get_parser,
    load_from_toml,
)
from openhands.core.config.utils import get_agent_config_arg
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import AgentFinishAction, CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

DATASET_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data')


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': functools.partial(codeact_user_response, encapsulate_solution=True),
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have solved the question, please use the finish tool and include your final answer in the message parameter of the finish tool. Your final answer MUST be encapsulated within <solution> and </solution>.\n'
}


def get_config(
    metadata: EvalMetadata,
) -> OpenHandsConfig:
    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'nikolaik/python-nodejs:python3.12-nodejs22'
    config = OpenHandsConfig(
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
    if metadata.agent_config:
        config.set_agent_config(metadata.agent_config, metadata.agent_class)
    else:
        logger.info('Agent config not provided, using default settings')
        agent_config = config.get_agent_config(metadata.agent_class)
        agent_config.enable_prompt_extensions = False

    config_copy = copy.deepcopy(config)
    load_from_toml(config_copy)
    if config_copy.search_api_key:
        config.search_api_key = SecretStr(config_copy.search_api_key)
    return config


def initialize_runtime(
    runtime: Runtime,
    instance: pd.Series,  # this argument is not required
):
    """Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f'{"-" * 50} BEGIN Runtime Initialization Fn {"-" * 50}')
    obs: CmdOutputObservation

    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    if instance['file_name'] != '':
        # if this question comes with a file, we need to save it to the workspace
        assert metadata.data_split is not None
        src_file = os.path.join(
            DATASET_CACHE_DIR, '2023', metadata.data_split, instance['file_name']
        )
        assert os.path.exists(src_file)
        dest_file = os.path.join('/workspace', instance['file_name'])
        runtime.copy_to(src_file, dest_file)

        # rename to file.extension_name
        extension_name = instance['file_name'].split('.')[-1]
        action = CmdRunAction(
            command=f'mv /workspace/{instance["file_name"]} /workspace/file.{extension_name}'
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        assert obs.exit_code == 0

    action = CmdRunAction(command='cd /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    logger.info(f'{"-" * 50} END Runtime Initialization Fn {"-" * 50}')


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
) -> EvalOutput:
    config = get_config(metadata)

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance['instance_id'], log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance["instance_id"]}.')

    if instance['file_name'] != '':
        extension_name = instance['file_name'].split('.')[-1]
        dest_file = os.path.join('/workspace', f'file.{extension_name}')
    else:
        dest_file = None

    # Prepare instruction
    instruction = """You have one question to answer. It is paramount that you provide a correct answer.
Give it all you can: I know for a fact that you have access to all the relevant tools to solve it and find the correct answer (the answer does exist). Failure or 'I cannot answer' or 'None found' will not be tolerated, success will be rewarded.
You must make sure you find the correct answer! You MUST strictly follow the task-specific formatting instructions for your final answer.
Here is the task:
{task_question}
""".format(
        task_question=instance['Question'],
    )
    logger.info(f'Instruction: {instruction}')
    if dest_file:
        instruction += f'\n\nThe mentioned file is provided in the workspace at: {dest_file.split("/")[-1]}'

    instruction += """IMPORTANT: When seeking information from a website, REFRAIN from arbitrary URL navigation. You should utilize the designated search engine tool with precise keywords to obtain relevant URLs or use the specific website's search interface. DO NOT navigate directly to specific URLs as they may not exist.\n\nFor example: if you want to search for a research paper on Arxiv, either use the search engine tool with specific keywords or navigate to arxiv.org and then use its interface.\n"""
    instruction += 'IMPORTANT: You should NEVER ask for Human Help.\n'
    instruction += 'IMPORTANT: Please encapsulate your final answer (answer ONLY) within <solution> and </solution>. Your answer will be evaluated using string matching approaches so it important that you STRICTLY adhere to the output formatting instructions specified in the task (e.g., alphabetization, sequencing, units, rounding, decimal places, etc.)\n'
    instruction += (
        'For example: The answer to the question is <solution> 42 </solution>.\n'
    )
    instruction += "IMPORTANT: Your final answer should be a number OR as few words as possible OR a comma separated list of numbers and/or strings. If you are asked for a number, express it numerically (i.e., with digits rather than words), do not use commas, and do not include units such as $ or percent signs unless specified otherwise. If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities). If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string.\n"

    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(metadata.agent_class, '')
    logger.info(f'Instruction:\n{instruction}', extra={'msg_type': 'OBSERVATION'})

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
    # ======= Attempt to evaluate the agent's edits =======
    # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    model_answer_raw = ''
    # get the last message or thought from the agent
    for event in reversed(state.history):
        if event.source == 'agent':
            if isinstance(event, AgentFinishAction):
                model_answer_raw = event.final_thought
                break
            elif isinstance(event, CmdRunAction):
                model_answer_raw = event.thought
                break
            elif isinstance(event, MessageAction):
                model_answer_raw = event.content
                break

    # attempt to parse model_answer
    model_answer = re.findall(r'<solution>(.*?)</solution>', model_answer_raw)
    if len(model_answer) == 0:
        logger.warning(f'Failed to parse model answer: {model_answer_raw}')
        model_answer = model_answer_raw
    else:
        model_answer = model_answer[0]

    logger.info(
        f'Final message: {model_answer} | Ground truth: {instance["Final answer"]}'
    )
    score = question_scorer(
        model_answer=model_answer, ground_truth=instance['Final answer']
    )
    test_result = {
        'score': score,
        'model_answer_raw': model_answer_raw,
        'model_answer': model_answer,
        'ground_truth': instance['Final answer'],
    }
    metrics = state.metrics.get() if state.metrics else None

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # Save the output
    output = EvalOutput(
        instance_id=instance['instance_id'],
        instance=instance.to_dict(),
        instruction=instance['Question'],
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result=test_result,
    )
    runtime.close()
    return output


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '--level',
        type=str,
        help='gaia level to evaluate, eg. 2023_level1',
    )
    parser.add_argument(
        '--data-split',
        type=str,
        help='data split to evaluate, eg. test',
        default='validation',
    )
    args, _ = parser.parse_known_args()

    agent_config = None
    if args.agent_config:
        agent_config = get_agent_config_arg(args.agent_config)

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False

    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    toml_config = OpenHandsConfig()
    load_from_toml(toml_config)
    metadata = make_metadata(
        llm_config=llm_config,
        dataset_name='gaia',
        agent_class=args.agent_cls,
        max_iterations=args.max_iterations,
        eval_note=args.eval_note,
        eval_output_dir=args.eval_output_dir,
        data_split=args.data_split,
        details={
            'gaia-level': args.level,
            'mcp-servers': ['tavily'] if toml_config.search_api_key else [],
        },
        agent_config=agent_config,
    )

    dataset = load_dataset('gaia-benchmark/GAIA', args.level)
    huggingface_hub.snapshot_download(
        'gaia-benchmark/GAIA',
        repo_type='dataset',
        local_dir=DATASET_CACHE_DIR,
    )
    gaia_tests = dataset[metadata.data_split].to_pandas()
    gaia_tests.rename(columns={'task_id': 'instance_id'}, inplace=True)

    output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
    prepared_dataset = prepare_dataset(gaia_tests, output_file, args.eval_n_limit)

    run_evaluation(
        dataset=prepared_dataset,
        metadata=metadata,
        output_file=output_file,
        num_workers=args.eval_num_workers,
        process_instance_func=process_instance,
    )
