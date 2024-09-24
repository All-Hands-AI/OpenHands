import argparse
import json

import numpy as np
import pandas as pd

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Summarize AiderBench results')
    parser.add_argument('input_filepath', type=str, help='Path to the JSONL file')
    args = parser.parse_args()

    # Create DataFrame from JSONL file
    df = pd.read_json(args.input_filepath, lines=True)

    df['cost'] = df['metrics'].apply(pd.Series)['accumulated_cost']
    df['result'] = (
        df['test_result'].apply(pd.Series)['exit_code'].map({0: 'Pass', 1: 'Fail'})
    )
    df['num_actions'] = pd.Series([len(a) - 1 for a in df['history']])

    passed = np.sum(df['result'] == 'Pass')
    total = df.shape[0]
    resolve_rate = round((passed / total) * 100, 2)

    print('Number of passed tests:', f'{passed}/{total} {resolve_rate:.2f}%')
    print('\nDescriptive statistics for number of actions:')
    print(df['num_actions'].describe())
    print('\nDescriptive statistics for costs:')
    print(df['cost'].describe())

    # Bin counts for actions
    action_bins = pd.cut(df['num_actions'], bins=range(0, 32, 2))
    print('\nAction bin counts:')
    print(action_bins.value_counts().sort_index())

    # Bin counts for costs
    cost_bins = pd.cut(df['cost'], bins=10)
    print('\nCost bin counts:')
    print(cost_bins.value_counts().sort_index())

    print(
        f'\nPassed {passed} tests, failed {total - passed} tests, resolve rate = {resolve_rate:.2f}%'
    )
    passed_tests = df[df['result'] == 'Pass']['instance_id'].tolist()
    failed_tests = df[df['result'] == 'Fail']['instance_id'].tolist()
    print('PASSED TESTS:')
    print(sorted(passed_tests))
    print('FAILED TESTS:')
    print(sorted(failed_tests))

    report_filepath = args.input_filepath.replace('.jsonl', '.report.json')
    print(f'Report writing to {report_filepath}')
    with open(report_filepath, 'w') as f:
        f.write(
            json.dumps(
                {
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'resolve_rate': resolve_rate,
                    'num_actions': df['num_actions'].describe().to_dict(),
                    'cost': df['cost'].describe().to_dict(),
                },
                indent=4,
            )
        )
