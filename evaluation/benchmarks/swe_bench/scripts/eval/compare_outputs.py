#!/usr/bin/env python3
import argparse

import pandas as pd

parser = argparse.ArgumentParser(
    description='Compare two swe_bench output JSONL files and print the resolved diff'
)
parser.add_argument('input_file_1', type=str)
parser.add_argument('input_file_2', type=str)
args = parser.parse_args()

df1 = pd.read_json(args.input_file_1, orient='records', lines=True)
df2 = pd.read_json(args.input_file_2, orient='records', lines=True)


# Get the intersection of the instance_ids
df = pd.merge(df1, df2, on='instance_id', how='inner')


def _get_resolved(report):
    if report is None:
        return False
    if isinstance(report, float):
        return False
    else:
        return report.get('resolved', False)


df['resolved_x'] = df['report_x'].apply(_get_resolved)
df['resolved_y'] = df['report_y'].apply(_get_resolved)
df['diff'] = df.apply(lambda x: x['resolved_x'] != x['resolved_y'], axis=1)

df_diff = df[df['diff']].sort_values(
    by=['resolved_x', 'resolved_y'], ascending=[False, False]
)
# skip if any of the resolved is nan, which means one of the eval is not finished yet
df_diff = df_diff[df_diff['resolved_x'].notna() & df_diff['resolved_y'].notna()]

print(f'X={args.input_file_1}')
print(f'Y={args.input_file_2}')
print(f'# diff={df_diff.shape[0]}')
df_diff = df_diff[['instance_id', 'resolved_x', 'resolved_y', 'report_x', 'report_y']]

# x resolved but y not
print('-' * 100)
df_diff_x_only = df_diff[df_diff['resolved_x'] & ~df_diff['resolved_y']].sort_values(
    by='instance_id'
)
print(f'# x resolved but y not={df_diff_x_only.shape[0]}')
print(df_diff_x_only[['instance_id', 'report_x', 'report_y']])

# y resolved but x not
print('-' * 100)
df_diff_y_only = df_diff[~df_diff['resolved_x'] & df_diff['resolved_y']].sort_values(
    by='instance_id'
)
print(f'# y resolved but x not={df_diff_y_only.shape[0]}')
print(df_diff_y_only[['instance_id', 'report_x', 'report_y']])
# get instance_id from df_diff_y_only
print('-' * 100)
print('Instances that x resolved but y not:')
print(df_diff_x_only['instance_id'].tolist())

print('-' * 100)
print('Instances that y resolved but x not:')
print(df_diff_y_only['instance_id'].tolist())
