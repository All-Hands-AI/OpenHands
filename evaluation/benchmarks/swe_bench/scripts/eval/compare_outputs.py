#!/usr/bin/env python3
import argparse
import os

import pandas as pd
from termcolor import colored

parser = argparse.ArgumentParser(
    description='Compare two swe_bench output JSONL files and print the resolved diff'
)
parser.add_argument('input_file_1', type=str)
parser.add_argument('input_file_2', type=str)
parser.add_argument(
    '--show-paths',
    action='store_true',
    help='Show visualization paths for failed instances',
)
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

x_only_by_repo = {}
for instance_id in df_diff_x_only['instance_id'].tolist():
    repo = instance_id.split('__')[0]
    x_only_by_repo.setdefault(repo, []).append(instance_id)
y_only_by_repo = {}
for instance_id in df_diff_y_only['instance_id'].tolist():
    repo = instance_id.split('__')[0]
    y_only_by_repo.setdefault(repo, []).append(instance_id)

print('-' * 100)
print(
    colored('Repository comparison (x resolved vs y resolved):', 'cyan', attrs=['bold'])
)
all_repos = sorted(set(list(x_only_by_repo.keys()) + list(y_only_by_repo.keys())))

# Calculate diffs and sort repos by diff magnitude
repo_diffs = []
for repo in all_repos:
    x_count = len(x_only_by_repo.get(repo, []))
    y_count = len(y_only_by_repo.get(repo, []))
    diff = abs(x_count - y_count)
    repo_diffs.append((repo, diff))

# Sort by diff (descending) and then by repo name
repo_diffs.sort(key=lambda x: (-x[1], x[0]))
threshold = max(
    3, sum(d[1] for d in repo_diffs) / len(repo_diffs) * 1.5 if repo_diffs else 0
)

x_input_file_folder = os.path.join(os.path.dirname(args.input_file_1), 'output.viz')

for repo, diff in repo_diffs:
    x_instances = x_only_by_repo.get(repo, [])
    y_instances = y_only_by_repo.get(repo, [])

    # Determine if this repo has a significant diff
    is_significant = diff >= threshold
    repo_color = 'red' if is_significant else 'yellow'

    print(f"\n{colored(repo, repo_color, attrs=['bold'])}:")
    print(colored(f'Difference: {diff} instances!', repo_color, attrs=['bold']))
    print(colored(f'X resolved but Y failed: ({len(x_instances)} instances)', 'green'))
    if x_instances:
        print('  ' + str(x_instances))
    print(colored(f'Y resolved but X failed: ({len(y_instances)} instances)', 'red'))
    if y_instances:
        print('  ' + str(y_instances))
        if args.show_paths:
            print(
                colored('    Visualization path for X failed:', 'cyan', attrs=['bold'])
            )
            for instance_id in y_instances:
                instance_file = os.path.join(
                    x_input_file_folder, f'false.{instance_id}.md'
                )
                print(f'    {instance_file}')
