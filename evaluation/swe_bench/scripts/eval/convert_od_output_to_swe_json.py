import argparse
import os

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('od_output_file', type=str)
args = parser.parse_args()
output_filepath = args.od_output_file.replace('.jsonl', '.swebench.jsonl')
print(f'Converting {args.od_output_file} to {output_filepath}')

od_format = pd.read_json(args.od_output_file, orient='records', lines=True)
# model name is the folder name of od_output_file
model_name = os.path.basename(os.path.dirname(args.od_output_file))


def process_git_patch(patch):
    if not patch.strip():
        # skip empty patches
        return ''

    patch = patch.replace('\r\n', '\n')
    # There might be some weird characters at the beginning of the patch
    # due to some OpenDevin inference command outputs

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
    return {
        'instance_id': row['instance_id'],
        'model_patch': process_git_patch(row['git_patch']),
        'model_name_or_path': model_name,
    }


swebench_format = od_format.apply(convert_row_to_swebench_format, axis=1)
swebench_format.to_json(output_filepath, lines=True, orient='records')
