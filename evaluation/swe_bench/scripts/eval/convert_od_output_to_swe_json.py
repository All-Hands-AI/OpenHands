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


def convert_row_to_swebench_format(row):
    return {
        'instance_id': row['instance_id'],
        'model_patch': row['git_patch'].replace('\r\n', '\n'),
        'model_name_or_path': model_name,
    }


swebench_format = od_format.apply(convert_row_to_swebench_format, axis=1)
swebench_format.to_json(output_filepath, lines=True, orient='records')
