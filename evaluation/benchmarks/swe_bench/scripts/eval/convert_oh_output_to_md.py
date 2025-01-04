#!/usr/bin/env python3
"""Convert OpenHands output to a readable markdown format for visualization."""

import argparse
import json
import os

import pandas as pd
from tqdm import tqdm

from evaluation.benchmarks.swe_bench.eval_infer import process_git_patch
from openhands.events.serialization import event_from_dict

tqdm.pandas()

parser = argparse.ArgumentParser()
parser.add_argument('oh_output_file', type=str)
args = parser.parse_args()
output_md_folder = args.oh_output_file.replace('.jsonl', '.viz')
print(f'Converting {args.oh_output_file} to markdown files in {output_md_folder}')

oh_format = pd.read_json(args.oh_output_file, orient='records', lines=True)

swebench_eval_file = args.oh_output_file.replace('.jsonl', '.swebench_eval.jsonl')
if os.path.exists(swebench_eval_file):
    eval_output_df = pd.read_json(swebench_eval_file, orient='records', lines=True)
else:
    eval_output_df = None

# model name is the folder name of oh_output_file
model_name = os.path.basename(os.path.dirname(args.oh_output_file))


def convert_history_to_str(history):
    ret = ''
    separator = '\n\n' + '-' * 100 + '\n'

    for i, event in enumerate(history):
        if i != 0:
            ret += separator

        if isinstance(event, list):
            # "event" is a legacy pair of (action, observation)
            event_obj = event_from_dict(event[0])
            ret += f'## {i+1}| {event_obj.__class__.__name__}\n\n'
            ret += str(event_obj)
            ret += separator

            event_obj = event_from_dict(event[1])
            ret += f'## {i+1}| {event_obj.__class__.__name__}\n\n'
            ret += str(event_obj)
        else:
            # "event" is a single event
            event_obj = event_from_dict(event)
            ret += f'## {i+1}| {event_obj.__class__.__name__}\n\n'
            ret += str(event_obj)
    return ret


def write_row_to_md_file(row, instance_id_to_test_result):
    if 'git_patch' in row:
        model_patch = row['git_patch']
    elif 'test_result' in row and 'git_patch' in row['test_result']:
        model_patch = row['test_result']['git_patch']
    else:
        raise ValueError(f'Row {row} does not have a git_patch')

    test_output = None
    if row['instance_id'] in instance_id_to_test_result:
        report = instance_id_to_test_result[row['instance_id']].get('report', {})
        resolved = report.get('resolved', False)
        test_output = instance_id_to_test_result[row['instance_id']].get(
            'test_output', None
        )
    elif 'report' in row and row['report'] is not None:
        if not isinstance(row['report'], dict):
            resolved = None
            print(
                f'ERROR: Report is not a dict, but a {type(row["report"])}. Row: {row}'
            )
        else:
            resolved = row['report'].get('resolved', False)
    else:
        resolved = None

    instance_id = row['instance_id']
    filename = f'{str(resolved).lower()}.{instance_id}.md'
    os.makedirs(output_md_folder, exist_ok=True)
    filepath = os.path.join(output_md_folder, filename)

    with open(filepath, 'w') as f:
        f.write(f'# {instance_id} (resolved: {resolved})\n')

        # MetaData
        f.write('## MetaData\n')
        f.write('```json\n')
        f.write(json.dumps(row['metadata'], indent=2))
        f.write('\n```\n')

        # Trajectory
        f.write('## History\n')
        f.write(convert_history_to_str(row['history']))

        f.write('## Model Patch\n')
        f.write(f'{process_git_patch(model_patch)}\n')

        f.write('## Test Output\n')
        f.write(str(test_output))


instance_id_to_test_result = {}
if eval_output_df is not None:
    instance_id_to_test_result = (
        eval_output_df[['instance_id', 'test_result']]
        .set_index('instance_id')['test_result']
        .to_dict()
    )

oh_format.progress_apply(
    write_row_to_md_file, axis=1, instance_id_to_test_result=instance_id_to_test_result
)
