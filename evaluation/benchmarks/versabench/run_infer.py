import argparse
import os
import re
import shutil
import subprocess

from ruamel.yaml import YAML

from openhands.core.logger import openhands_logger as logger

evaluation_path = 'evaluation/benchmarks/'


def check_config_vbackup(path):
    vbackup = os.path.join(path, 'config_vbackup.toml')
    if os.path.exists(vbackup):
        if os.environ.get('preserve_vconfigs'):
            shutil.move(vbackup, os.path.join(path, 'config.toml'))
        else:
            raise RuntimeError(
                'Versabench backups config files from individual benchmarks to restore after evaluation.'
                f'A backup file already exists ({vbackup}). Probably because an evaluation was ended prematurely'
                'If you want to preserve the already existing backups, you can export preserve_vconfigs="true" and rerun'
                f'Otherwise sort the backups by hand to continue.'
            )


def copy_config(output_path, input_path):
    check_config_vbackup(output_path)

    config_file = os.path.join(output_path, 'config.toml')
    vbackup_file = os.path.join(output_path, 'config_vbackup.toml')

    if os.path.exists(config_file):
        shutil.move(config_file, vbackup_file)

    os.makedirs(output_path, exist_ok=True)
    print(f'Copying {input_path} to {output_path}')

    if not input_path or not os.path.exists(os.path.join(input_path, 'config.toml')):
        open(config_file, 'a').close()  # touch
    else:
        shutil.copy(os.path.join(input_path, 'config.toml'), config_file)


def restore_config(path):
    config_file = os.path.join(path, 'config.toml')
    vbackup_file = os.path.join(path, 'config_vbackup.toml')

    if os.path.exists(config_file):
        os.remove(config_file)

    if os.path.exists(vbackup_file):
        shutil.move(vbackup_file, config_file)


def update_lca_config(llm_model):
    config_path = './evaluation/benchmarks/lca_ci_build_repair/config.yaml'

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f'{config_path} not found. This file must exist. Please refer to the lca_ci_build_repair README.'
        )

    yaml = YAML()
    with open(config_path, 'r') as f:
        config = yaml.load(f)

    exp_name = os.environ.get('EXP_NAME', '')
    short_llm_model = llm_model.split('.', 1)[-1][:10]
    config['model_name'] = f'OH-{short_llm_model}-{exp_name}'

    with open(config_path, 'w') as f:
        yaml.dump(config, f)


def run_single_benchmark(benchmark, config_path, command):
    logger.info(f'Starting sub-benchmark {benchmark}')
    versabench_dir = os.path.dirname(os.path.realpath(__file__))

    if config_path:
        full_config_path = os.path.join(
            versabench_dir, 'splits', config_path, benchmark
        )
    else:
        full_config_path = ''

    output_path = os.path.join(
        evaluation_path, re.search(r'benchmarks/([^/]+)', command).group(1)
    )

    copy_config(output_path, full_config_path)

    env = os.environ.copy()  # inherit current environment with micromamba active
    cwd = os.getcwd()  # preserve current directory

    # Run subprocess and capture stdout and stderr
    result = subprocess.run(
        ['/bin/zsh', '-c', command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=cwd,
        text=True,  # Return strings rather than bytes
    )

    if result.returncode != 0:
        logger.error(f'Command failed with exit code {result.returncode}')
        logger.error(f'Command stderr output:\n{result.stderr}')
        logger.error(f'Command stdout output:\n{result.stdout}')
        # Raise exception to maintain the same behavior as before with check=True
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=command,
            output=result.stdout,
            stderr=result.stderr,
        )

    logger.info(f'Finished sub-benchmark {benchmark}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', default='', help='Optional split name')
    parser.add_argument('--llm', help='LLM name')
    parser.add_argument('--workers', default='8', help='Default number of workers')
    parser.add_argument('--gaia', action='store_true', help='Run inference on gaia')
    parser.add_argument(
        '--commit0', action='store_true', help='Run inference on commit0'
    )
    parser.add_argument('--swe', action='store_true', help='Run inference on swe bench')
    parser.add_argument('--swt', action='store_true', help='Run inference on swt bench')
    parser.add_argument(
        '--multimodal', action='store_true', help='Run inference on multimdoal'
    )
    parser.add_argument(
        '--multi-swe', action='store_true', help='Run inference on multi swe bench'
    )
    parser.add_argument(
        '--lca-ci', action='store_true', help='Run inference on lca ci build repair'
    )
    parser.add_argument(
        '--the-agent-company',
        action='store_true',
        help='Run inference on the agent company ',
    )
    args = parser.parse_args()

    all = not (
        args.lca_ci
        or args.the_agent_company
        or args.gaia
        or args.multimodal
        or args.swe
        or args.swt
        or args.multi_swe
        or args.commit0
    )
    if all:
        logger.info('Running all benchmarks')
    else:
        logger.info('Running only selected benchmarks')

    if all or args.lca_ci:
        update_lca_config(args.llm)
        run_single_benchmark(
            'lca_ci_build_repair',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX=""; ./evaluation/benchmarks/lca_ci_build_repair/scripts/run_infer.sh {args.llm} HEAD CodeActAgent 100 100 1',
        )
    if all or args.the_agent_company:
        the_agent_company_tmp_dir = './evaluation/benchmarks/versabench/versabench_cache/the_agent_company_tmp_dir'
        run_single_benchmark(
            'the_agent_company',
            args.split,
            f'export TMPDIR={the_agent_company_tmp_dir};export EVAL_DOCKER_IMAGE_PREFIX=""; ./evaluation/benchmarks/the_agent_company/scripts/run_infer.sh --agent-llm-config {args.llm} --env-llm-config {args.llm} --server-hostname localhost --version 1.0.0 --start-percentile 50 --end-percentile 100 --agent-config CodeActAgent',
        )
    if all or args.gaia:
        # Reminder: add your Tavily API key
        run_single_benchmark(
            'gaia',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX=""; export checkout_eval_branch=true ; ./evaluation/benchmarks/gaia/scripts/run_infer.sh {args.llm} "" CodeActAgent 100 "" {args.workers}',
        )
    if all or args.multimodal:
        run_single_benchmark(
            'multimodal',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images";  ./evaluation/benchmarks/swe_bench/scripts/run_infer.sh {args.llm} HEAD CodeActAgent 100 100 {args.workers} princeton-nlp/SWE-bench_Multimodal test ',
        )
    if all or args.multi_swe:
        # Reminder: run install.sh to download the dataset
        run_single_benchmark(
            'multi_swe_bench',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX=""; ./evaluation/benchmarks/multi_swe_bench/scripts/run_infer.sh {args.llm} HEAD CodeActAgent 100 100 {args.workers} ./evaluation/benchmarks/versabench/versabench_cache/Multi-SWE-bench/java/all/all_updated_clean.jsonl java',
        )
    if all or args.commit0:
        run_single_benchmark(
            'commit0',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX="docker.io/wentingzhao" ; ./evaluation/benchmarks/commit0/scripts/run_infer.sh lite {args.llm} HEAD CodeActAgent 500 100 {args.workers} wentingzhao/commit0_combined test',
        )
    if all or args.swe:
        run_single_benchmark(
            'swe_bench',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" ; ./evaluation/benchmarks/swe_bench/scripts/run_infer.sh {args.llm}  HEAD CodeActAgent 100 100 {args.workers} princeton-nlp/SWE-bench_Verified test 1',
        )
    if all or args.swt:
        run_single_benchmark(
            'swt_bench',
            args.split,
            f'export EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" ; ./evaluation/benchmarks/swe_bench/scripts/run_infer.sh {args.llm}  HEAD CodeActAgent 100 100 {args.workers} princeton-nlp/SWE-bench_Verified test 1 swt',
        )


if __name__ == '__main__':
    main()
