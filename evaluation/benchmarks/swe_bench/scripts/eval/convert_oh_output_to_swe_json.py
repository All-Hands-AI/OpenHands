import argparse
import os

import pandas as pd

from evaluation.benchmarks.swe_bench.eval_infer import process_git_patch

parser = argparse.ArgumentParser()
parser.add_argument('oh_output_file', type=str)
args = parser.parse_args()
output_filepath = args.oh_output_file.replace('.jsonl', '.swebench.jsonl')
print(f'Converting {args.oh_output_file} to {output_filepath}')

oh_format = pd.read_json(args.oh_output_file, orient='records', lines=True)
# model name is the folder name of oh_output_file
model_name = os.path.basename(os.path.dirname(args.oh_output_file))


def convert_row_to_swebench_format(row):
    if 'git_patch' in row:
        model_patch = row['git_patch']
    elif 'test_result' in row and 'git_patch' in row['test_result']:
        model_patch = row['test_result']['git_patch']
    else:
        print(f'WARNING: Row {row} does not have a git_patch')
        model_patch = ''

    return {
        'instance_id': row['instance_id'],
        'model_patch': process_git_patch(model_patch),
        'model_name_or_path': model_name,
    }


swebench_format = oh_format.apply(convert_row_to_swebench_format, axis=1)
swebench_format.to_json(output_filepath, lines=True, orient='records')
