#!/usr/bin/env python3

import json
import sys

def convert_dataset(input_file, output_file):
    """Convert dataset from Multi-SWE format to SWE-bench format"""
    
    with open(input_file, 'r') as f:
        data = json.load(f) if input_file.endswith('.json') else [json.loads(line) for line in f]
    
    converted_data = []
    
    for item in data:
        # Convert to SWE-bench format
        converted_item = {
            "instance_id": item.get("instance_id", f"{item.get('org', 'unknown')}__{item.get('repo', 'unknown')}-{item.get('number', '0')}"),
            "repo": f"{item.get('org', 'unknown')}/{item.get('repo', 'unknown')}",
            "base_commit": item.get("base", {}).get("sha", "unknown"),
            "patch": item.get("fix_patch", ""),
            "test_patch": item.get("test_patch", ""),
            "problem_statement": item.get("body", ""),
            "hints_text": "",
            "created_at": "2024-01-01",
            "version": "1.0",
            "FAIL_TO_PASS": item.get("failed_tests", []),
            "PASS_TO_PASS": item.get("fixed_tests", []),
            "environment_setup_commit": item.get("base", {}).get("sha", "unknown"),
            "selected_ids": [item.get("instance_id", f"{item.get('org', 'unknown')}__{item.get('repo', 'unknown')}-{item.get('number', '0')}")]
        }
        converted_data.append(converted_item)
    
    with open(output_file, 'w') as f:
        for item in converted_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"Converted {len(converted_data)} items from {input_file} to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_dataset.py <input_file> <output_file>")
        sys.exit(1)
    
    convert_dataset(sys.argv[1], sys.argv[2])