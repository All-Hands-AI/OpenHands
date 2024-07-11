import argparse
import json
import os
from collections import defaultdict

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('input_file', type=str)
args = parser.parse_args()

dirname = os.path.dirname(args.input_file)
report_json = os.path.join(dirname, 'report.json')

df = pd.read_json(args.input_file, lines=True)

output_md_filepath = os.path.join(dirname, 'README.md')
instance_id_to_status = defaultdict(
    lambda: {'resolved': False, 'empty_generation': False}
)
if os.path.exists(report_json):
    with open(report_json, 'r') as f:
        report = json.load(f)

    output_md = (
        "# SWE-bench Report\n"
        "This folder contains the evaluation results of the SWE-bench using the [official evaluation docker containerization](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md#choosing-the-right-cache_level).\n\n"
        "## Summary\n"
        f"- total instances: {report['total_instances']}\n"
        f"- submitted instances: {report['submitted_instances']}\n"
        f"- completed instances: {report['completed_instances']}\n"
        f"- empty patch instances: {report['empty_patch_instances']}\n"
        f"- resolved instances: {report['resolved_instances']}\n"
        f"- unresolved instances: {report['unresolved_instances']}\n"
        f"- error instances: {report['error_instances']}\n"
        f"- unstopped instances: {report['unstopped_instances']}\n"
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

    # Apply the status to the dataframe
    def apply_report(row):
        instance_id = row['instance_id']
        if instance_id in instance_id_to_status:
            return dict(instance_id_to_status[instance_id])
        return row.get('report', {})

    df['report'] = df.apply(apply_report, axis=1)


if os.path.exists(args.input_file + '.bak'):
    conf = input('Existing backup file found. Do you want to overwrite it? (y/n)')
    if conf != 'y':
        exit()
    os.remove(args.input_file + '.bak')

# backup the original file
os.rename(args.input_file, args.input_file + '.bak')
df.to_json(args.input_file, orient='records', lines=True)

with open(output_md_filepath, 'w') as f:
    f.write(output_md)
