import argparse
import json
from pathlib import Path

def main(predictions_path):
    predictions_path = Path(predictions_path)
    report_path = predictions_path.parent / "report.json"

    total = 0
    resolved = 0
    resolved_ids = []
    unresolved_ids = []

    with predictions_path.open() as f:
        for line in f:
            total += 1
            data = json.loads(line)
            inst_id = data.get("instance_id")
            result = data.get("test_result", {}).get("eval_result", {})
            if result.get("num_passed") == result.get("num_tests"):
                resolved += 1
                resolved_ids.append(inst_id)
            else:
                unresolved_ids.append(inst_id)

    report = {
        "total_instances": total,
        "submitted_instances": total,
        "completed_instances": total,
        "resolved_instances": resolved,
        "unresolved_instances": total - resolved,
        "empty_patch_instances": 0,
        "error_instances": 0,
        "completed_ids": total,
        "incomplete_ids": total,
        "empty_patch_ids": [],
        "submitted_ids": [],
        "resolved_ids": resolved_ids,
        "unresolved_ids": unresolved_ids,
        "error_ids": []
    }

    with report_path.open("w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions .jsonl file")
    args = parser.parse_args()
    main(args.predictions)

