import json
import argparse
import logging


import unidiff
from unidiff import PatchSet

from evaluation.benchmarks.swe_bench.resource.constants import MAP_VERSION_TO_INSTALL

_LOGGER = logging.getLogger(__name__)


def remove_setup_files(model_patch: str):
    """ Discard all changes that a patch applies to files changes by the pre_install script and that are reproduction scripts (top-level script)"""
    setup_files = ["setup.py", "tox.ini", "pyproject.toml"]
    pre_install = MAP_VERSION_TO_INSTALL.get(exec_spec.repo, {}).get(exec_spec.version, {}).get("pre_install", [])
    relevant_files = [
        file
        for file in setup_files
        if any(file in install and "sed" in install for install in pre_install)
    ]
    patch = unidiff.PatchSet(model_patch)
    to_delete = []
    for i, file in enumerate(patch):
        if any(f in file.source_file for f in relevant_files) or file.target_file.count("/") == 1:
            to_delete.append(i)
    for i in reversed(to_delete):
        del patch[i]
    return str(patch)


# extract everything under "2025-02-12 17:11:03,241 - INFO - Got git diff for instance astropy__astropy-6938:"

def main(
        prediction_file: str,
        ci_mode: bool = False,
):
    with open(prediction_file) as f:
        for line in f:
            pred = json.loads(line)
            try:
                git_diff = pred["test_result"]["git_patch"]
            except KeyError:
                _LOGGER.warning("No git diff found for instance %s", pred["instance_id"])
                continue
            try:
                patchset = PatchSet(git_diff)
            except:
                _LOGGER.warning("Invalid git diff found for instance %s", pred["instance_id"])
            try:
                print(json.dumps({
                    "instance_id": pred["instance_id"],
                    "model_name_or_path": "OpenHands-Claude-Sonnet-3.5",
                    "model_patch": git_diff,
                    "full_output": json.dumps(pred),
                }))
            except KeyError:
                _LOGGER.warning("No git diff found for instance %s", pred["instance_id"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prediction_file",
        type=str,
        required=True,
        help="Path to the prediction file (.../outputs.jsonl)",
    )
    parser.add_argument(
        "--ci_mode",
        action="store_true",
        help="Whether agent was run in CI mode, with pre-install set up. Set flag if infer was run with `swt-ci`.",
    )
    args = parser.parse_args()

    main(args.prediction_file, args.ci_mode)
