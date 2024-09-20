import argparse
import os

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('oh_output_file', type=str)
args = parser.parse_args()
output_filepath = args.oh_output_file.replace('.jsonl', '.swebench.jsonl')
print(f'Converting {args.oh_output_file} to {output_filepath}')

oh_format = pd.read_json(args.oh_output_file, orient='records', lines=True)
# model name is the folder name of oh_output_file
model_name = os.path.basename(os.path.dirname(args.oh_output_file))


def process_git_patch(patch):
    if not isinstance(patch, str):
        return ''

    if not patch.strip():
        # skip empty patches
        return ''

    patch = patch.replace('\r\n', '\n')
    # There might be some weird characters at the beginning of the patch
    # due to some OpenHands inference command outputs

    # FOR EXAMPLE:
    # git diff --no-color --cached 895f28f9cbed817c00ab68770433170d83132d90
    # [A[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[C[K0
    # diff --git a/django/db/models/sql/.backup.query.py b/django/db/models/sql/.backup.query.py
    # new file mode 100644
    # index 0000000000..fc13db5948

    # We "find" the first line that starts with "diff" and then we remove lines before it
    lines = patch.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('diff --git'):
            patch = '\n'.join(lines[i:])
            break

    patch = patch.rstrip() + '\n'  # Make sure the last line ends with a newline
    return patch


def convert_row_to_swebench_format(row):
    if 'git_patch' in row:
        model_patch = row['git_patch']
    elif 'test_result' in row and 'git_patch' in row['test_result']:
        model_patch = row['test_result']['git_patch']
    else:
        raise ValueError(f'Row {row} does not have a git_patch')

    return {
        'instance_id': row['instance_id'],
        'model_patch': process_git_patch(model_patch),
        'model_name_or_path': model_name,
    }


swebench_format = oh_format.apply(convert_row_to_swebench_format, axis=1)
swebench_format.to_json(output_filepath, lines=True, orient='records')
