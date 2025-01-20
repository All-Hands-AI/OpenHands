#!/usr/bin/env python3
import argparse

import pandas as pd

parser = argparse.ArgumentParser(
    description='Compare two TestGenEval output JSONL files and print the resolved diff'
)
parser.add_argument('input_file_1', type=str)
parser.add_argument('input_file_2', type=str)
args = parser.parse_args()

df1 = pd.read_json(args.input_file_1, orient='records', lines=True)
df2 = pd.read_json(args.input_file_2, orient='records', lines=True)


# Get the intersection of the ids
df = pd.merge(df1, df2, on='id', how='inner')


def _get_coverage(report):
    if report is None:
        return False
    if isinstance(report, float):
        return False
    else:
        return report.get('test_pass', False)


df['test_pass_x'] = df['test_pass_x'].apply(_get_coverage)
df['test_pass_y'] = df['test_pass_y'].apply(_get_coverage)
df['diff'] = df.apply(lambda x: x['test_pass_x'] != x['test_pass_y'], axis=1)

df_diff = df[df['diff']].sort_values(
    by=['test_pass_x', 'test_pass_y'], ascending=[False, False]
)
# skip if any of the pass is nan, which means one of the eval is not finished yet
df_diff = df_diff[df_diff['test_pass_x'].notna() & df_diff['test_pass_y'].notna()]

print(f'X={args.input_file_1}')
print(f'Y={args.input_file_2}')
print(f'# diff={df_diff.shape[0]}')
df_diff = df_diff[['id', 'test_pass_x', 'test_pass_y', 'report_x', 'report_y']]

# x pass but y not
print('-' * 100)
df_diff_x_only = df_diff[df_diff['test_pass_x'] & ~df_diff['test_pass_y']].sort_values(
    by='id'
)
print(f'# x pass but y not={df_diff_x_only.shape[0]}')
print(df_diff_x_only[['id', 'report_x', 'report_y']])

# y pass but x not
print('-' * 100)
df_diff_y_only = df_diff[~df_diff['test_pass_x'] & df_diff['test_pass_y']].sort_values(
    by='id'
)
print(f'# y pass but x not={df_diff_y_only.shape[0]}')
print(df_diff_y_only[['id', 'report_x', 'report_y']])
# get instance_id from df_diff_y_only
print('-' * 100)
print('Instances that x pass but y not:')
print(df_diff_x_only['id'].tolist())

print('-' * 100)
print('Instances that y pass but x not:')
print(df_diff_y_only['id'].tolist())
