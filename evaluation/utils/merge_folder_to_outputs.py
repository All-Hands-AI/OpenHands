import argparse
import json
import os
from glob import glob

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('output_dir', type=str, help='Path to the folder to merge')
args = parser.parse_args()

mr_output_dir = os.path.join(args.output_dir, 'mr_outputs')
output_file = os.path.join(args.output_dir, 'output.jsonl')
assert os.path.exists(mr_output_dir) and os.path.isdir(mr_output_dir)

files = glob(os.path.join(mr_output_dir, '*.json'))
if len(files) == 0:
    print('No files found, exiting')
    exit(0)

print(f'Found {len(files)} files in {mr_output_dir}')
data = []
for file in files:
    with open(file, 'r') as f:
        data.append(json.load(f))

if not os.path.exists(output_file):
    existing_df = pd.DataFrame()
    existing_instance_ids = set()
    print(f'No existing output file {output_file}, creating new one.')
else:
    existing_df = pd.read_json(output_file, lines=True, orient='records')
    existing_instance_ids = set(existing_df['instance_id'].tolist())
    print(f'Original output file {output_file} has {len(existing_df)} rows')

df_to_concat = []
for d in data:
    if d['instance_id'] not in existing_instance_ids:
        df_to_concat.append(d)

if len(df_to_concat) == 0:
    print('No new rows to add, exiting')
    exit(0)

if os.path.exists(output_file):
    existing_df.to_json(output_file + '.bak', lines=True, orient='records')

new_df = pd.concat([existing_df, pd.DataFrame(df_to_concat)], ignore_index=True)
print(f'New combined output file {output_file} has {len(new_df)} rows.')
new_df.to_json(output_file, lines=True, orient='records')
