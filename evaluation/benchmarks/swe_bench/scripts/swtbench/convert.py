import argparse
import json
import logging

import unidiff

from evaluation.benchmarks.swe_bench.resource.swt_bench_constants import (
    MAP_VERSION_TO_INSTALL,
)

_LOGGER = logging.getLogger(__name__)


def remove_setup_files(model_patch: str, instance: dict, delete_setup_changes: bool):
    """Discard all changes that a patch applies to files changes by the pre_install script and that are reproduction scripts (top-level script)"""
    setup_files = ['setup.py', 'tox.ini', 'pyproject.toml']
    pre_install = (
        MAP_VERSION_TO_INSTALL.get(instance['repo'], {})
        .get(instance['version'], {})
        .get('pre_install', [])
    )
    relevant_files = (
        [
            file
            for file in setup_files
            if any(file in install and 'sed' in install for install in pre_install)
        ]
        if delete_setup_changes
        else []
    )
    for i in range(10):
        try:
            # Appearently outputs.jsonl has .strip() applied, so we try to reconstruct the original patch by adding auxiliary whitespace
            patch = unidiff.PatchSet(model_patch + i * '\n')
            break
        except unidiff.UnidiffParseError:
            pass

    to_delete = []
    for i, file in enumerate(patch):
        if (
            any(f in file.source_file for f in relevant_files)
            or file.target_file.count('/') == 1
        ):
            to_delete.append(i)
    for i in reversed(to_delete):
        del patch[i]
    return str(patch)


def main(
    prediction_file: str,
):
    """Main function to extract the model patches from the OpenHands prediction file and turn them into the expected SWT-Bench format."""
    with open(prediction_file) as f:
        for line in f:
            pred = json.loads(line)
            try:
                git_diff = pred['test_result']['git_patch']
            except KeyError:
                _LOGGER.warning(
                    'Warning: No git diff found for instance %s', pred['instance_id']
                )
                continue
            ci_mode = pred['metadata']['details'].get('mode', '') == 'swt-ci'
            try:
                git_diff = remove_setup_files(git_diff, pred['instance'], ci_mode)
            except:  # noqa: E722
                _LOGGER.warning(
                    'Warning: Invalid git diff found for instance %s',
                    pred['instance_id'],
                )
            print(
                json.dumps(
                    {
                        'instance_id': pred['instance_id'],
                        'model_name_or_path': f'{pred["metadata"]["llm_config"]["openrouter_app_name"]}__{pred["metadata"]["agent_class"]}__{pred["metadata"]["llm_config"]["model"]}',
                        'model_patch': git_diff,
                        'full_output': json.dumps(pred),
                    }
                )
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--prediction_file',
        type=str,
        required=True,
        help='Path to the prediction file (.../outputs.jsonl)',
    )
    args = parser.parse_args()

    main(args.prediction_file)
