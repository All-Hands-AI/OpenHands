import os
import shutil
import subprocess
import argparse
import json
from pathlib import Path

def update_multi_swe_config(output_jsonl_path, config_path, dataset):
    path_to_parent = os.path.dirname(os.path.abspath(output_jsonl_path))
    converted_path = os.path.join(path_to_parent, "output_converted.jsonl")

    # Run the conversion script
    subprocess.run([
        "python3", "./evaluation/benchmarks/multi_swe_bench/scripts/eval/convert.py",
        "--input", output_jsonl_path,
        "--output", converted_path
    ], check=True)

    # Create required directories
    os.makedirs(os.path.join(path_to_parent, "eval_files", "dataset"), exist_ok=True)
    os.makedirs(os.path.join(path_to_parent, "eval_files", "workdir"), exist_ok=True)
    os.makedirs(os.path.join(path_to_parent, "eval_files", "repos"), exist_ok=True)
    os.makedirs(os.path.join(path_to_parent, "eval_files", "logs"), exist_ok=True)

    # Prepare config dict
    config = {
        "mode": "evaluation",
        "workdir": os.path.join(path_to_parent, "eval_files", "workdir"),
        "patch_files": [converted_path],
        "dataset_files": [dataset],
        "force_build": True,
        "output_dir": os.path.join(path_to_parent, "eval_files", "dataset"),
        "specifics": [],
        "skips": [],
        "repo_dir": os.path.join(path_to_parent, "eval_files", "repos"),
        "need_clone": True,
        "global_env": [],
        "clear_env": True,
        "stop_on_error": False,
        "max_workers": 5,
        "max_workers_build_image": 5,
        "max_workers_run_instance": 5,
        "log_dir": os.path.join(path_to_parent, "eval_files", "logs"),
        "log_level": "DEBUG",
        "fix_patch_run_cmd": (
            "bash -c \"apt update ; apt install -y patch ; "
            "sed -i 's@git apply.*@patch --batch --fuzz=5 -p1 -i /home/test.patch;"
            "patch --batch --fuzz=5 -p1 -i /home/fix.patch@g' /home/fix-run.sh ; chmod +x /home/*.sh  ; /home/fix-run.sh\""
        )
    }

    # Save to multibench.config
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to input file")
    parser.add_argument("--output", required=True, help="Path to create config")
    parser.add_argument("--dataset", required=True, help="Path to dataset")
    args = parser.parse_args()

    update_multi_swe_config(args.input, args.output, args.dataset)
