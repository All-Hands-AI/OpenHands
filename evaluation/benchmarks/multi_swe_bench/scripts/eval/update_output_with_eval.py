import argparse
import json
import os
from collections import defaultdict

from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('input_file', type=str)
parser.add_argument('--force', action='store_true', 
                    help='Force update all reports even if no changes are detected')
parser.add_argument('--overwrite-backup', action='store_true',
                    help='Automatically overwrite existing backup files without prompting')
args = parser.parse_args()

dirname = os.path.dirname(args.input_file)

# Initialize counters and data structures
instance_id_to_status = defaultdict(
    lambda: {
        'empty_generation': False,
        'resolved': False,
        'failed_apply_patch': False,
        'error_eval': False,
        'test_timeout': False,
    }
)

# Process official report if it exists
swebench_official_report_json = os.path.join(dirname, 'eval_files/dataset/final_report.json')
openhands_remote_report_jsonl = args.input_file.replace(
    '.jsonl', '.swebench_eval.jsonl'
)

if os.path.exists(swebench_official_report_json):
    output_md_filepath = os.path.join(dirname, 'README.md')
    with open(swebench_official_report_json, 'r') as f:
        report = json.load(f)
    
    # Convert instance IDs from "repo/name:pr-123" format to "repo__name-123" format
    def convert_instance_id(instance_id):
        """Convert instance ID from slash/colon-pr format to double underscore/dash format"""
        if '/' in instance_id and ':pr-' in instance_id:
            # Split on '/' and ':pr-'
            parts = instance_id.split('/')
            if len(parts) == 2:
                repo_part = parts[0]
                name_and_pr = parts[1]
                if ':pr-' in name_and_pr:
                    name, pr_number = name_and_pr.split(':pr-')
                    return f"{repo_part}__{name}-{pr_number}"
        return instance_id
    
    # Convert all instance ID lists in the report
    for key in ['resolved_ids', 'unresolved_ids', 'error_ids', 'empty_patch_ids', 'incomplete_ids']:
        if key in report:
            report[key] = [convert_instance_id(instance_id) for instance_id in report[key]]

    output_md = (
        '# Multi-SWE-bench Report\n'
        'This folder contains the evaluation results of the SWE-bench using the [official evaluation docker containerization](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md#choosing-the-right-cache_level).\n\n'
        '## Summary\n'
        f'- total instances: {report["total_instances"]}\n'
        f'- submitted instances: {report["submitted_instances"]}\n'
        f'- completed instances: {report["completed_instances"]}\n'
        f'- empty patch instances: {report["empty_patch_instances"]}\n'
        f'- resolved instances: {report["resolved_instances"]}\n'
        f'- unresolved instances: {report["unresolved_instances"]}\n'
        f'- error instances: {report["error_instances"]}\n'
    )

    output_md += '\n## Resolved Instances\n'
    # instance_id to status
    for instance_id in report['resolved_ids']:
        instance_id_to_status[instance_id]['resolved'] = True
        output_md += (
            f'- [{instance_id}](./eval_outputs/{instance_id}/run_instance.log)\n'
        )

    output_md += '\n## Unresolved Instances\n'
    for instance_id in report['unresolved_ids']:
        output_md += (
            f'- [{instance_id}](./eval_outputs/{instance_id}/run_instance.log)\n'
        )

    output_md += '\n## Error Instances\n'
    for instance_id in report['error_ids']:
        instance_id_to_status[instance_id]['error_eval'] = True
        output_md += (
            f'- [{instance_id}](./eval_outputs/{instance_id}/run_instance.log)\n'
        )

    output_md += '\n## Empty Patch Instances\n'
    for instance_id in report['empty_patch_ids']:
        instance_id_to_status[instance_id]['empty_generation'] = True
        output_md += (
            f'- [{instance_id}](./eval_outputs/{instance_id}/run_instance.log)\n'
        )

    output_md += '\n## Incomplete Instances\n'
    for instance_id in report['incomplete_ids']:
        output_md += (
            f'- [{instance_id}](./eval_outputs/{instance_id}/run_instance.log)\n'
        )

    with open(output_md_filepath, 'w') as f:
        f.write(output_md)

else:
    print(
        f'No report file found: Both {swebench_official_report_json} and {openhands_remote_report_jsonl} do not exist.'
    )
    exit()

# Before backup and update, check if any changes would be made (unless --force is used)
if not args.force:
    needs_update = False
    with open(args.input_file, 'r') as infile:
        for line in tqdm(infile, desc='Checking for changes'):
            data = json.loads(line)
            instance_id = data['instance_id']
            current_report = data.get('report', {})
            new_report = instance_id_to_status[
                instance_id
            ]  # if no report, it's not resolved
            if current_report != new_report:
                needs_update = True
                break

    if not needs_update:
        print('No updates detected. Skipping file update.')
        exit()
else:
    print('Force flag enabled. Updating all reports regardless of changes.')

# Backup and update the original file row by row
if os.path.exists(args.input_file + '.bak'):
    if args.overwrite_backup:
        print('Existing backup file found. Overwriting automatically due to --overwrite-backup flag.')
        os.remove(args.input_file + '.bak')
    else:
        conf = input('Existing backup file found. Do you want to overwrite it? (y/n)')
        if conf != 'y':
            exit()
        os.remove(args.input_file + '.bak')

os.rename(args.input_file, args.input_file + '.bak')

# Process and write file row by row
with (
    open(args.input_file + '.bak', 'r') as infile,
    open(args.input_file, 'w') as outfile,
):
    for line in tqdm(infile, desc='Updating output file'):
        data = json.loads(line)
        instance_id = data['instance_id']
        data['report'] = instance_id_to_status[instance_id]
        outfile.write(json.dumps(data) + '\n')
