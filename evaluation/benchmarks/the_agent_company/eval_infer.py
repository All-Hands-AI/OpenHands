import argparse
import json
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-folder", required=True, help="Path to folder with eval_*.json files")
    args = parser.parse_args()

    eval_folder = Path(args.eval_folder)
    eval_files = list(eval_folder.glob("eval_*.json"))

    report = {
        "total_instances": len(eval_files),
        "submitted_instances": len(eval_files),
        "completed_instances": len(eval_files),
        "resolved_instances": 0,
        "unresolved_instances": 0,
        "empty_patch_instances": 0,
        "error_instances": 0,
        "completed_ids": [],
        "incomplete_ids": [],
        "empty_patch_ids": [],
        "submitted_ids": [],
        "resolved_ids": [],
        "unresolved_ids": [],
        "error_ids": [],
    }

    for file in eval_files:
        try:
            with open(file) as f:
                data = json.load(f)

            total = data.get("final_score", {}).get("total", 0)
            result = data.get("final_score", {}).get("result", 0)

            if total == result:
                report["resolved_instances"] += 1
                report["resolved_ids"].append(file.name)
            else:
                report["unresolved_instances"] += 1
                report["unresolved_ids"].append(file.name)

        except Exception:
            report["error_instances"] += 1
            report["error_ids"].append(file.name)

    with open(eval_folder / "report.json", "w") as out:
        json.dump(report, out, indent=2)

if __name__ == "__main__":
    main()

