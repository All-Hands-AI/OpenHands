"""Implements evaluation on JetBrains CI builds repair baselines

Please see https://github.com/JetBrains-Research/lca-baselines/tree/main/ci-builds-repair
and https://huggingface.co/datasets/JetBrains-Research/lca-ci-builds-repair

TODOs:
- Add more flags
"""

import json
import os
from pathlib import Path

import ruamel.yaml

from evaluation.utils.shared import (
    EvalMetadata,
    get_default_sandbox_config_for_eval,
    make_metadata,
)
from openhands.core.config import (
    LLMConfig,
    OpenHandsConfig,
    get_parser,
    load_openhands_config,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.main import create_runtime
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_async_from_sync


def get_config(
    metadata: EvalMetadata,
) -> OpenHandsConfig:
    sandbox_config = get_default_sandbox_config_for_eval()
    sandbox_config.base_container_image = 'python:3.12-bookworm'
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
    agent_config = config.get_agent_config(metadata.agent_class)
    agent_config.enable_prompt_extensions = False
    return config


config = load_openhands_config()


def load_bench_config():
    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )  # Get the absolute path of the script
    config_path = os.path.join(script_dir, 'config.yaml')
    yaml = ruamel.yaml.YAML(typ='rt')
    with open(config_path, 'r') as file:
        return yaml.load(file)


bench_config = load_bench_config()


def run_eval(
    runtime: Runtime,
):
    """Run the evaluation and create report"""
    logger.info(f'{"-" * 50} BEGIN Runtime Initialization Fn {"-" * 50}')
    obs: CmdOutputObservation

    lca_path = bench_config['LCA_PATH']
    lca_ci_path = os.path.join(
        lca_path, 'lca-baselines', 'ci-builds-repair', 'ci-builds-repair-benchmark'
    )

    model_name = bench_config['model_name']

    action = CmdRunAction(command=f'mkdir {lca_path}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command=f'cd {lca_path}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    lca_repo_url = 'https://github.com/juanmichelini/lca-baselines'
    action = CmdRunAction(command=f'git clone {lca_repo_url}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command=f'cd {lca_ci_path}')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    action = CmdRunAction(command='git switch open-hands-integration')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert obs.exit_code == 0

    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )  # Get the absolute path of the script
    config_path = os.path.join(script_dir, 'config.yaml')
    runtime.copy_to(config_path, lca_ci_path)

    token_gh = bench_config['token_gh']
    commandf = f'export TOKEN_GH={token_gh}'
    action = CmdRunAction(command=commandf)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)

    action = CmdRunAction(command='poetry install')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)

    # Set up the task environment
    commandf = f'poetry run python run_eval_jobs.py --model-name "{model_name}" --config-path "{lca_ci_path}/config.yaml" --job-ids-file "/tmp/output_lca.jsonl" --result-filename "testfile.jsonl"  > /tmp/single_output.txt'
    action = CmdRunAction(command=commandf)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(f'run_eval_jobs.py gave {obs.content} !')
    # assert obs.exit_code == 0

    commandf = 'cat /tmp/single_output.txt'
    action = CmdRunAction(command=commandf)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(f' {commandf} gave {obs.content}!')

    testfile_path = os.path.join(bench_config['out_folder'], 'testfile.jsonl')
    commandf = f'cat {testfile_path}'
    action = CmdRunAction(command=commandf)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    report_str = obs.content

    logger.info(f'{"-" * 50} END Runtime Initialization Fn {"-" * 50}')
    return report_str


def process_predictions(predictions_path: str):
    output_path = Path(predictions_path)
    if output_path.suffix != '.jsonl':
        raise ValueError('output_path must end in .jsonl')

    output_lca_path = output_path.with_name(output_path.stem + '_lca.jsonl')

    with output_path.open() as infile, output_lca_path.open('w') as outfile:
        for line in infile:
            data = json.loads(line)
            json.dump(data.get('test_result'), outfile)
            outfile.write('\n')

    return str(output_lca_path)


if __name__ == '__main__':
    parser = get_parser()
    parser.add_argument(
        '-s',
        '--eval-split',
        type=str,
        default='test',
        choices=['test'],
        help='data split to evaluate on, must be test',
    )
    parser.add_argument(
        '--predictions-path',
        type=str,
        help='Path to the directory containing the output.jsonl with the predictions.',
    )
    args, _ = parser.parse_known_args()

    data_split = args.eval_split

    llm_config = LLMConfig(model='dummy_model')

    metadata = make_metadata(
        llm_config,
        f'jetbrains-lca-ci--{data_split}',
        args.agent_cls,
        args.max_iterations,
        args.eval_note,
        args.predictions_path,
    )

    # prepare image
    config = get_config(metadata)
    runtime = create_runtime(config)
    call_async_from_sync(runtime.connect)
    logger.info('Converting output.jsonl into output_lca.jsonl')
    predictions_lca_path = process_predictions(
        os.path.join(args.predictions_path, 'output.jsonl')
    )
    runtime.copy_to(predictions_lca_path, '/tmp')

    # get results
    results_str = run_eval(runtime)
    results_path = os.path.join(args.predictions_path, 'results.jsonl')
    with open(results_path, 'w') as file:
        file.write(results_str)
    logger.info(f'Saved results to {results_path}')

    # make a summary
    resolved_instances = []
    unresolved_instances = []
    for line in results_str.strip().splitlines():
        data = json.loads(line)
        conclusion = data.get('conclusion')
        if conclusion == 'success':
            resolved_instances.append(data)
        elif conclusion == 'failure':
            unresolved_instances.append(data)

    completed_instances = resolved_instances + unresolved_instances

    report = {
        'success': len(resolved_instances),
        'failure': len(unresolved_instances),
        'resolved_instances': resolved_instances,
        'unresolved_instances': unresolved_instances,
        'completed_instances': completed_instances,
    }

    print(f'Results: {report}')
    report_path = os.path.join(args.predictions_path, 'report.jsonl')
    with open(report_path, 'w') as out_f:
        out_f.write(json.dumps(report) + '\n')

    logger.info(f'Saved report of results in swebench format to {report_path}')
