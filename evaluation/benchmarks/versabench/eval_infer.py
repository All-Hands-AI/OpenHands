import argparse
import json
import os
import subprocess
from pathlib import Path

from openhands.core.logger import openhands_logger as logger


def update_multi_swe_config(output_jsonl_path):
    path_to_parent = os.path.dirname(os.path.abspath(output_jsonl_path))
    converted_path = os.path.join(path_to_parent, 'output_converted.jsonl')

    # Run the conversion script
    subprocess.run(
        [
            'python3',
            './evaluation/benchmarks/multi_swe_bench/scripts/eval/convert.py',
            '--input',
            output_jsonl_path,
            '--output',
            converted_path,
        ],
        check=True,
    )

    # Create required directories
    os.makedirs(os.path.join(path_to_parent, 'eval_files', 'dataset'), exist_ok=True)
    os.makedirs(os.path.join(path_to_parent, 'eval_files', 'workdir'), exist_ok=True)
    os.makedirs(os.path.join(path_to_parent, 'eval_files', 'repos'), exist_ok=True)
    os.makedirs(os.path.join(path_to_parent, 'eval_files', 'logs'), exist_ok=True)

    # Prepare config dict
    config = {
        'mode': 'evaluation',
        'workdir': os.path.join(path_to_parent, 'eval_files', 'workdir'),
        'patch_files': [converted_path],
        'dataset_files': [os.path.abspath('./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/all/all.jsonl')],
        'force_build': True,
        'output_dir': os.path.join(path_to_parent, 'eval_files', 'dataset'),
        'specifics': [],
        'skips': [],
        'repo_dir': os.path.join(path_to_parent, 'eval_files', 'repos'),
        'need_clone': True,
        'global_env': [],
        'clear_env': True,
        'stop_on_error': False,
        'max_workers': 5,
        'max_workers_build_image': 5,
        'max_workers_run_instance': 5,
        'log_dir': os.path.join(path_to_parent, 'eval_files', 'logs'),
        'log_level': 'DEBUG',
        'fix_patch_run_cmd': 'bash -c "apt update && apt install -y patch && sed -i \'s@git apply.*@patch --batch --fuzz=5 -p1 -i /home/test.patch;@\' /home/fix-run.sh && chmod +x /home/*.sh  && /home/fix-run.sh"',
    }

    # Save to multibench.config
    config_path =  os.path.join(path_to_parent, 'multibench.config.json')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    return config_path


def eval_benchmark(benchmark, command):
    logger.info(f'Starting evaluating sub-benchmark {benchmark}')
    env = os.environ.copy()  # inherit current environment with micromamba active
    cwd = os.getcwd()  # preserve current directory
    result = subprocess.run(['/bin/zsh', '-c', command], check=True, env=env, cwd=cwd)
    if result.returncode != 0:
        print(f'Command failed with exit code {result.returncode}')
    logger.info(f'Finished evaluating sub-benchmark {benchmark}')


def main():
    parser = argparse.ArgumentParser(description='Run benchmarks selectively.')
    parser.add_argument('--gaia', type=str, default='')
    parser.add_argument('--commit0', type=str, default='')
    parser.add_argument('--swe', type=str, default='')
    parser.add_argument('--swt', type=str, default='')
    parser.add_argument('--multimodal', type=str, default='')
    parser.add_argument('--multi-swe', type=str, default='')
    parser.add_argument('--lca-ci', type=str, default='')
    parser.add_argument('--the-agent-company', type=str, default='')

    args = parser.parse_args()

    if args.gaia:
        gaia_report = args.gaia[: -len('output.jsonl')] + 'report.txt'
        eval_benchmark(
            'gaia',
            f'python ./evaluation/benchmarks/gaia/get_score.py --file {args.gaia} | tee {gaia_report}',
        )
        print(f'Report saved to {gaia_report}')
    if args.commit0:
        eval_benchmark(
            'commit0',
            f'./evaluation/benchmarks/commit0/scripts/eval_infer.sh  {args.commit0}',
        )
    if args.swe:
        command = f'export RUNTIME=""; ./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh {args.swe} ""  princeton-nlp/SWE-bench_Verified test'
        print(f'swe command: {command}')
        eval_benchmark('swe', command)
    if args.swt:
        args.swt = os.path.abspath(args.swt)
        eval_note = Path(args.swt).resolve().parent.name
        swt_converted = args.swt.removesuffix('.jsonl') + '_swt_converted.jsonl'
        convert = f'python3 evaluation/benchmarks/swe_bench/scripts/swtbench/convert.py --prediction_file {args.swt} > {swt_converted}'
        inner_report = f' python3 -m src.main --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path {swt_converted} --max_workers 12 --run_id {eval_note} --patch_types vanilla  --build_mode api'
        report = f'(pushd ./evaluation/benchmarks/versabench/versabench_cache/swt-bench && source .venv/bin/activate && {inner_report} && popd)'
        eval_benchmark('swt', f'{convert} ; {report}')
    if args.multimodal:
        eval_benchmark(
            'multimodal',
            f'export RUNTIME=""; ./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh {args.multimodal}  "" princeton-nlp/SWE-bench_Multimodal test',
        )
    if args.multi_swe:
        config_path = update_multi_swe_config(args.multi_swe)
        eval_benchmark(
            'multi-swe',
            f'pip install multi-swe-bench ; python -m multi_swe_bench.harness.run_evaluation --config {config_path}',
        )
    if args.lca_ci:
        if args.lca_ci.endswith('output.jsonl'):
            args.lca_ci = args.lca_ci[: -len('output.jsonl')]
        eval_benchmark(
            'lca-ci',
            f'./evaluation/benchmarks/lca_ci_build_repair/scripts/eval_infer.sh  {args.lca_ci}',
        )
    if args.the_agent_company:
        eval_benchmark(
            'the-agent-company',
            f'./evaluation/benchmarks/the_agent_company/scripts/eval_infer.sh  {args.the_agent_company}',
        )


if __name__ == '__main__':
    main()
