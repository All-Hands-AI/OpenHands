import asyncio
import json
import os

import git
import pandas as pd

from evaluation.benchmarks.discoverybench.eval_utils.eval_w_subhypo_gen import (
    run_eval_gold_vs_gen_NL_hypo_workflow,
)
from evaluation.benchmarks.discoverybench.eval_utils.response_parser import (
    extract_gen_hypo_from_logs,
)
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
    AgentConfig,
    AppConfig,
    SandboxConfig,
    get_llm_config_arg,
    parse_arguments,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import AgentFinishAction, CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync

EVALUATION_LLM = 'gpt-4-1106-preview'

DATA_FILES = {}

LIBRARIES = [
    'pandas',
    'numpy',
    'scipy',
    'matplotlib',
    'seaborn',
    'scikit-learn',
    'statsmodels',
]

AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please finish the interaction using the "finish" tool.\n'
}


def get_config(
    metadata: EvalMetadata,
) -> AppConfig:
    config = AppConfig(
        default_agent=metadata.agent_class,
        run_as_openhands=False,
        runtime='docker',
        max_iterations=metadata.max_iterations,
        sandbox=SandboxConfig(
            base_container_image='python:3.12-bookworm',
            enable_auto_lint=True,
            use_host_network=False,
        ),
        # do not mount workspace
        workspace_base=None,
        workspace_mount_path=None,
    )
    config.set_llm_config(metadata.llm_config)
    agent_config = AgentConfig(
        function_calling=False,
        codeact_enable_jupyter=True,
        codeact_enable_browsing_delegate=True,
    )
    config.set_agent_config(agent_config)
    return config


def get_dv_query_for_real(
    datasets, question, domain_knowledge=None, workflow_tags=None
):
    """
    Prepare a structured query for the agent to execute on the specified datasets.

    This function constructs a query by compiling metadata from the provided datasets, along with any relevant domain knowledge and workflow tags.

    Args:
        datasets: List of datasets
        question: Query to be answered
        domain_knowledge: Domain knowledge if any
        workflow_tags: Workflow tags if any

    Returns:
        query_to_dv: Query to be run on the dataset
        dataset_meta: Metadata of the dataset
    """

    dataset_meta = ''
    for dataset_metadata in datasets:
        dataset_meta += 'Dataset name: ' + dataset_metadata['name']
        dataset_meta += 'Dataset description: ' + dataset_metadata['description']
        dataset_meta += '\nBrief description of columns: '
        for col in dataset_metadata['columns']['raw']:
            dataset_meta += col['name'] + ': ' + col['description'] + ', '

    query_to_dv = dataset_meta

    query_to_dv += f'\nQuery: {question}'

    if domain_knowledge:
        query_to_dv += (
            '\nAdditionally, we provide some hints that might be useful to solve the task. Domain Knowledge: \n'
            + domain_knowledge
            + '.\n'
        )

    if workflow_tags:
        query_to_dv += 'The meta tags are: ' + workflow_tags + '.\n'

    query_to_dv += (
        'In the final answer, please write down a scientific hypothesis in '
        'natural language, derived from the provided dataset, clearly stating the '
        'context of hypothesis (if any), variables chosen (if any) and '
        'relationship between those variables (if any) including any statistical significance.'
        'Also generate a summary of the full workflow starting from data loading that led to the final answer as WORKFLOW SUMMARY:'
    )

    # Run the NL query through datavoyager
    return query_to_dv, dataset_meta


def initialize_runtime(runtime: Runtime, data_files: list[str]):
    """
    Initialize the runtime for the agent.

    This function is called before the runtime is used to run the agent.
    """
    logger.info(f"{'-' * 50} BEGIN Runtime Initialization Fn {'-' * 50}")
    obs: CmdOutputObservation

    action = CmdRunAction(command='mkdir -p /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command='cd /workspace')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    for file in data_files:
        runtime.copy_to(
            file,
            '/workspace',
        )

    for lib in LIBRARIES:
        action = CmdRunAction(command=f'pip install {lib}')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        assert obs.exit_code == 0

    logger.info(f"{'-' * 50} END Runtime Initialization Fn {'-' * 50}")


def get_last_agent_finish_action(state: State) -> AgentFinishAction:
    for event in reversed(state.history):
        if isinstance(event, AgentFinishAction):
            return event
    return None


def get_last_message_action(state: State) -> MessageAction:
    for event in reversed(state.history):
        if isinstance(event, MessageAction):
            return event
    return None


def complete_runtime(state: State):
    last_agent_finish_action = get_last_agent_finish_action(state)
    last_agent_message_action = get_last_message_action(state)

    if last_agent_finish_action is not None:
        final_message_1 = last_agent_finish_action.thought
        gen_hypo_1, gen_workflow_1, error_1 = extract_gen_hypo_from_logs(
            final_message_1
        )
    else:
        gen_hypo_1, gen_workflow_1, error_1 = '', '', ''

    if last_agent_message_action is not None:
        final_message_2 = last_agent_message_action.content
        gen_hypo_2, gen_workflow_2, error_2 = extract_gen_hypo_from_logs(
            final_message_2
        )
    else:
        gen_hypo_2, gen_workflow_2, error_2 = '', '', ''

    if gen_hypo_1 and gen_hypo_2:
        test_result = {
            'gen_hypo': last_agent_finish_action.thought
            if last_agent_finish_action
            else last_agent_message_action.content,
            'gen_workflow': '',
            'error': '',
        }
        return test_result

    test_result = {
        'gen_hypo': gen_hypo_1 if gen_hypo_1 else gen_hypo_2,
        'gen_workflow': gen_workflow_1 if gen_workflow_1 else gen_workflow_2,
        'error': error_1 if error_1 else error_2,
    }

    return test_result


def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    reset_logger: bool = True,
):
    """
    Process and evaluate a single instance of the dataset.

    This function executes the OpenHands agent
    for a specific instance of the dataset. It retrieves
    the agent's results and evaluates them against the gold
    hypothesis.

    Args:
        instance: A single row of the dataset
        metadata: Metadata for the evaluation
        reset_logger: Whether to reset the logger

    Returns:
        output: EvalOutput object
    """

    config = get_config(metadata)

    # Setup the logger properly, so you can run
    # multi-processing to parallelize the evaluation
    if reset_logger:
        log_dir = os.path.join(metadata.eval_output_dir, 'infer_logs')
        reset_logger_for_multiprocessing(logger, instance.instance_id, log_dir)
    else:
        logger.info(f'Starting evaluation for instance {instance.instance_id}.')

    problem_statement, dataset_metadata = get_dv_query_for_real(
        datasets=instance.datasets,
        question=instance.query,
        domain_knowledge=instance.domain_knowledge,
        workflow_tags=instance.workflow_tags,
    )

    # Prepare instruction
    instruction = (
        f'You are a discovery agent who can execute a python code only once to answer a query based on one or more datasets. The datasets will be present in the current directory.\n\n'
        'Environment has been set up for you to start working. You may assume all necessary tools and datasets are installed.\n\n'
        '# Problem Statement\n'
        f'{problem_statement}\n\n'
    )
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        'You should NOT modify any existing test case files. If needed, you can add new test cases in a NEW file to reproduce the issue.\n'
        'You SHOULD INCLUDE PROPER INDENTATION in your edit commands.\n'
    )
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX[metadata.agent_class]

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    initialize_runtime(runtime, instance.data_files)

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

    if state is None:
        raise ValueError('State should not be None.')

    metrics = state.metrics.get() if state.metrics else None
    test_result = complete_runtime(state)

    # history is now available as a stream of events, rather than list of pairs of (Action, Observation)
    # for compatibility with the existing output format, we can remake the pairs here
    # remove when it becomes unnecessary
    histories = compatibility_for_eval_history_pairs(state.history)

    # DiscoveryBench Evaluation
    eval_rec = run_eval_gold_vs_gen_NL_hypo_workflow(
        query=instance.query,
        gold_hypo=instance.gold_hypo,
        gold_workflow='',
        gen_hypo=test_result['gen_hypo'],
        gen_workflow='',
        dataset_meta=instance.dataset_metadata,
        llm_used=EVALUATION_LLM,
        dataset_type='real',
    )

    test_result['eval_rec'] = eval_rec

    output = EvalOutput(
        instance_id=str(instance.instance_id),
        instruction=instruction,
        metadata=metadata,
        history=histories,
        metrics=metrics,
        error=state.last_error if state and state.last_error else None,
        test_result=test_result,
    )

    return output


def update_csv_name(name):
    name = name.replace('-', '_')

    if 'meta_regression' in name:
        name = name.replace('meta_regression', 'meta-regression')
    if 'ML_enabled' in name:
        name = name.replace('ML_enabled', 'ML-enabled')

    return name


def list_csv_files(list_of_datasets):
    res = []
    for ele in list_of_datasets:
        for key, value in ele.items():
            if key == 'name':
                csv_file_name = update_csv_name(value)
                res.append(DATA_FILES[csv_file_name])
    return res


def create_dataset(repo_location: str, split: str = 'test'):
    """
    Create a dataset from the discoverybench repository
    by walking through the repository and extracting metadata
    from the metadata_{}.json files

    Args:
        repo_location: Location of the repository
        split: Split of the dataset to use

    Returns:
        df: DataFrame containing the dataset instances
    """

    data_dict = {}

    data_location = os.path.join(repo_location, 'discoverybench', 'real', split)
    answer_key_location = os.path.join(repo_location, 'eval', 'answer_key_real.csv')

    idx = 0

    for root, dirs, files in os.walk(data_location):
        for file in files:
            if file.endswith('.json'):
                if 'metadata' in file:
                    metadata = json.load(open(os.path.join(root, file)))

                    dataset = root.split('/')[-1]
                    metadata_id = file.split('_')[-1].split('.')[0]
                    domain = metadata.get('domain', '')
                    domain_knowledge = metadata.get('domain_knowledge', '')
                    workflow_tags = metadata.get('workflow_tags', '')
                    datasets = metadata.get('datasets', [])
                    queries = metadata.get('queries', [])
                    gold_workflow = metadata.get('workflow')

                    # loop through queries list to get queries
                    # and each query has qid; add that to dictionary
                    for query in queries[0]:
                        qid = query.get('qid', '')

                        data = {
                            'dataset': dataset,
                            'metadata_id': metadata_id,
                            'qid': qid,
                            'domain': domain,
                            'domain_knowledge': domain_knowledge,
                            'workflow_tags': workflow_tags,
                            'datasets': datasets,
                            'question_type': query['question_type'],
                            'query': query['question'],
                            'gold_workflow': gold_workflow,
                            'dataset_metadata': metadata,
                        }

                        data_dict[idx] = data
                        idx += 1

            if file.endswith('.csv'):
                DATA_FILES[file] = os.path.join(root, file)
            if file.endswith('.txt'):
                DATA_FILES[file] = os.path.join(root, file)

    df = pd.DataFrame.from_dict(data_dict, orient='index')

    df['instance_id'] = df.index

    df['data_files'] = df['datasets'].apply(lambda x: list_csv_files(x))

    answer_key = pd.read_csv(answer_key_location)

    answer_key = answer_key.rename(
        columns={
            'metadataid': 'metadata_id',
            'query_id': 'qid',
            'gold_hypothesis': 'gold_hypothesis',
        }
    )

    df['qid'] = df['qid'].astype(int)
    df['metadata_id'] = df['metadata_id'].astype(int)

    answer_key['qid'] = answer_key['qid'].astype(int)
    answer_key['metadata_id'] = answer_key['metadata_id'].astype(int)

    df = pd.merge(df, answer_key, on=['dataset', 'metadata_id', 'qid'], how='left')

    return df


if __name__ == '__main__':
    args = parse_arguments()

    # clone git repositor for csv files
    repo_url = 'https://github.com/allenai/discoverybench.git'
    repo_location = 'git-discoverybench-allenai'

    try:
        git.Repo.clone_from(repo_url, repo_location)
    except git.exc.GitCommandError:
        print('Repository already exists')

    dataset = create_dataset(repo_location)

    # check if there is any empty csv_file
    if dataset['data_files'].isnull().any():
        raise ValueError('Some csv files are missing.')

    llm_config = None
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        # modify_params must be False for evaluation purpose, for reproducibility and accurancy of results
        llm_config.modify_params = False
    if llm_config is None:
        raise ValueError(f'Could not find LLM config: --llm_config {args.llm_config}')

    metadata = make_metadata(
        llm_config,
        'discoverybench-python',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.eval_output_dir,
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
