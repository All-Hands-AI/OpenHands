import argparse
import json
import os
from collections import defaultdict

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('input_file', type=str)
args = parser.parse_args()

dirname = os.path.dirname(args.input_file)

df = pd.read_json(args.input_file, lines=True)

instance_id_to_status = defaultdict(
    lambda: {
        'empty_generation': False,
        'resolved': False,
        'failed_apply_patch': False,
        'error_eval': False,
        'test_timeout': False,
    }
)


# Apply the status to the dataframe
def apply_report(row):
    instance_id = row['instance_id']
    if instance_id in instance_id_to_status:
        return dict(instance_id_to_status[instance_id])
    return row.get('report', {})


swebench_official_report_json = os.path.join(dirname, 'report.json')
openhands_remote_report_jsonl = args.input_file.replace(
    '.jsonl', '.swebench_eval.jsonl'
)

if os.path.exists(swebench_official_report_json):
    output_md_filepath = os.path.join(dirname, 'README.md')
    with open(swebench_official_report_json, 'r') as f:
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

    df['report'] = df.apply(apply_report, axis=1)

    with open(output_md_filepath, 'w') as f:
        f.write(output_md)

elif os.path.exists(openhands_remote_report_jsonl):
    output_md_filepath = args.input_file.replace('.jsonl', '.swebench_eval.md')

    df_eval = pd.read_json(openhands_remote_report_jsonl, lines=True, orient='records')

    assert len(df['instance_id'].unique()) == len(
        df
    ), 'There are duplicate instance ids in the original output which is not allowed'
    assert len(df_eval['instance_id'].unique()) == len(
        df_eval
    ), 'There are duplicate instance ids in the eval report which is not allowed'

    for _, row in df_eval.iterrows():
        instance_id_to_status[row['instance_id']] = row['test_result']['report']
    df['report'] = df.apply(apply_report, axis=1)

    report_is_dict = df['report'].apply(lambda x: isinstance(x, dict))
    if not report_is_dict.all():
        print(df[~report_is_dict])
        raise ValueError(f'Report is not a dict, but a {type(row["report"])}')

    _n_instances = len(df)
    _n_resolved = len(df[df['report'].apply(lambda x: x.get('resolved', False))])
    _n_unresolved = _n_instances - _n_resolved
    _n_empty_patch = len(
        df[df['report'].apply(lambda x: x.get('empty_generation', False))]
    )
    _n_error = len(df[df['report'].apply(lambda x: x.get('error_eval', False))])
    output_md = (
        '# SWE-bench Report\n'
        'This folder contains the evaluation results of the SWE-bench using the [official evaluation docker containerization](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md#choosing-the-right-cache_level).\n\n'
        '## Summary\n'
        f'- submitted instances: {_n_instances}\n'
        f'- empty patch instances: {_n_empty_patch}\n'
        f'- resolved instances: {_n_resolved}\n'
        f'- unresolved instances: {_n_unresolved}\n'
        f'- error instances: {_n_error}\n'
    )

    def _instance_id_to_log_path(instance_id):
        path = f"{args.input_file.replace('.jsonl', '.swebench_eval.logs')}/instance_{instance_id}.log"
        # make it relative path
        path = os.path.relpath(path, start=dirname)
        return path

    output_md += '\n## Resolved Instances\n'
    # instance_id to status
    for instance_id in sorted(
        df[df['report'].apply(lambda x: x.get('resolved', False))][
            'instance_id'
        ].unique()
    ):
        instance_id_to_status[instance_id]['resolved'] = True
        output_md += f'- [{instance_id}]({_instance_id_to_log_path(instance_id)})\n'

    output_md += '\n## Unresolved Instances\n'
    for instance_id in sorted(
        df[~df['report'].apply(lambda x: x.get('resolved', False))][
            'instance_id'
        ].unique()
    ):
        output_md += f'- [{instance_id}]({_instance_id_to_log_path(instance_id)})\n'

    output_md += '\n## Error Instances\n'
    for instance_id in sorted(
        df[df['report'].apply(lambda x: x.get('error_eval', False))][
            'instance_id'
        ].unique()
    ):
        instance_id_to_status[instance_id]['error_eval'] = True
        output_md += f'- [{instance_id}]({_instance_id_to_log_path(instance_id)})\n'

    output_md += '\n## Empty Patch Instances\n'
    for instance_id in sorted(
        df[df['report'].apply(lambda x: x.get('empty_generation', False))][
            'instance_id'
        ].unique()
    ):
        instance_id_to_status[instance_id]['empty_generation'] = True
        output_md += f'- [{instance_id}]({_instance_id_to_log_path(instance_id)})\n'

    output_md += '\n## Incomplete Instances\n'
    for instance_id in sorted(
        df[df['report'].apply(lambda x: x.get('test_timeout', False))][
            'instance_id'
        ].unique()
    ):
        output_md += f'- [{instance_id}]({_instance_id_to_log_path(instance_id)})\n'
    with open(output_md_filepath, 'w') as f:
        f.write(output_md)
else:
    print(
        f'No report file found: Both {swebench_official_report_json} and {openhands_remote_report_jsonl} do not exist.'
    )
    exit()

if os.path.exists(args.input_file + '.bak'):
    conf = input('Existing backup file found. Do you want to overwrite it? (y/n)')
    if conf != 'y':
        exit()
    os.remove(args.input_file + '.bak')

# backup the original file
os.rename(args.input_file, args.input_file + '.bak')
df.to_json(args.input_file, orient='records', lines=True)
