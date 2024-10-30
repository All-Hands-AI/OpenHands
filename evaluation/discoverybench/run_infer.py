import json
import os

import git
import pandas as pd

from evaluation.utils.shared import (
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from openhands.core.config import (
    get_llm_config_arg,
    parse_arguments,
)

DATA_FILES = {}


def process_instance(instance, metadata, output_file): ...


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
