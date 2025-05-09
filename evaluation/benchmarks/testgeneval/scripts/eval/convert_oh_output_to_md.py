#!/usr/bin/env python3
"""Convert OpenHands output to a readable markdown format for visualization."""

import argparse
import json
import os

import pandas as pd
from tqdm import tqdm

from openhands.events.serialization import event_from_dict

tqdm.pandas()

parser = argparse.ArgumentParser()
parser.add_argument('oh_output_file', type=str)
args = parser.parse_args()
output_md_folder = args.oh_output_file.replace('.jsonl', '.viz')
print(f'Converting {args.oh_output_file} to markdown files in {output_md_folder}')

oh_format = pd.read_json(args.oh_output_file, orient='records', lines=True)
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
            ret += f'## {i + 1}| {event_obj.__class__.__name__}\n\n'
            ret += str(event_obj)
            ret += separator

            event_obj = event_from_dict(event[1])
            ret += f'## {i + 1}| {event_obj.__class__.__name__}\n\n'
            ret += str(event_obj)
        else:
            # "event" is a single event
            event_obj = event_from_dict(event)
            ret += f'## {i + 1}| {event_obj.__class__.__name__}\n\n'
            ret += str(event_obj)
    return ret


def write_row_to_md_file(row):
    if 'test_suite' in row:
        test_suite = row['test_suite']
    elif 'test_result' in row and 'test_suite' in row['test_result']:
        test_suite = row['test_result']['test_suite']
    else:
        raise ValueError(f'Row {row} does not have a test_suite')

    if 'report' in row:
        coverage = row['report'].get('coverage', 0)
        mutation = row['report'].get('mutation_score', 0)
    else:
        coverage = None
        mutation = None

    id = row['id']
    filename = f'{id}.md'
    os.makedirs(output_md_folder, exist_ok=True)
    filepath = os.path.join(output_md_folder, filename)

    with open(filepath, 'w') as f:
        f.write(f'# {id} (coverage: {coverage})\n')
        f.write(f'# {id} (mutation score: {mutation})\n')

        # MetaData
        f.write('## MetaData\n')
        f.write('```json\n')
        f.write(json.dumps(row['metadata'], indent=2))
        f.write('\n```\n')

        # Trajectory
        f.write('## History\n')
        f.write(convert_history_to_str(row['history']))

        f.write('## Test Suite\n')
        f.write(f'{test_suite}\n')


oh_format.progress_apply(write_row_to_md_file, axis=1)
