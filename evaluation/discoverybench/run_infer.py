import os

import git

from evaluation.utils.shared import (
    make_metadata,
    prepare_dataset,
    run_evaluation,
)
from openhands.core.config import (
    get_llm_config_arg,
    parse_arguments,
)


def process_instance(instance, metadata, output_file): ...


def create_dataset(repo_location): ...


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
