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

instance_id_to_status = defaultdict(dict)
if os.path.exists(report_json):
    with open(report_json, 'r') as f:
        report = json.load(f)

    # instance_id to status
    for status, instance_ids in report.items():
        for instance_id in instance_ids:
            if status == 'resolved':
                instance_id_to_status[instance_id]['resolved'] = True
            elif status == 'applied':
                instance_id_to_status[instance_id]['applied'] = True
            elif status == 'test_timeout':
                instance_id_to_status[instance_id]['test_timeout'] = True
            elif status == 'test_errored':
                instance_id_to_status[instance_id]['test_errored'] = True
            elif status == 'no_generation':
                instance_id_to_status[instance_id]['empty_generation'] = True

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
