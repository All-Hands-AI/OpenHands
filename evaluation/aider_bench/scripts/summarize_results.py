import argparse

import numpy as np
import pandas as pd


def extract_test_results(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    passed = []
    failed = []
    for _, row in df.iterrows():
        instance_id = row['instance_id']
        resolved = False
        if 'test_result' in row and 'exit_code' in row['test_result']:
            resolved = row['test_result']['exit_code'] == 0
        if resolved:
            passed.append(instance_id)
        else:
            failed.append(instance_id)
    return passed, failed


def visualize_results(df: pd.DataFrame):
    df1 = pd.DataFrame()
    df1['cost'] = df['metrics'].apply(pd.Series)['accumulated_cost']
    df1['result'] = (
        df['test_result'].apply(pd.Series)['exit_code'].map({0: 'Pass', 1: 'Fail'})
    )
    df1['actions'] = pd.Series([len(a) - 1 for a in df['history']])

    passed = np.sum(df1['result'] == 'Pass')
    total = df.shape[0]
    resolve_rate = round((passed / total) * 100, 2)

    print('Number of passed tests:', f'{passed}/{total} {resolve_rate:.2f}%')
    print('\nDescriptive statistics for number of actions:')
    print(df1['actions'].describe())
    print('\nDescriptive statistics for costs:')
    print(df1['cost'].describe())

    # Bin counts for actions
    action_bins = pd.cut(df1['actions'], bins=range(0, 32, 2))
    print('\nAction bin counts:')
    print(action_bins.value_counts().sort_index())

    # Bin counts for costs
    cost_bins = pd.cut(df1['cost'], bins=10)
    print('\nCost bin counts:')
    print(cost_bins.value_counts().sort_index())

    return resolve_rate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Summarize AiderBench results')
    parser.add_argument('input_filepath', type=str, help='Path to the JSONL file')
    args = parser.parse_args()

    # Create DataFrame from JSONL file
    df = pd.read_json(args.input_filepath, lines=True)

    passed_tests, failed_tests = extract_test_results(df)
    resolve_rate = visualize_results(df)

    print(
        f'\nPassed {len(passed_tests)} tests, failed {len(failed_tests)} tests, resolve rate = {resolve_rate:.2f}%'
    )
    print('PASSED TESTS:')
    print(passed_tests)
    print('FAILED TESTS:')
    print(failed_tests)
