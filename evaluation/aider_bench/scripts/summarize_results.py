import json
import os
import sys

import numpy as np
import pandas as pd

# Try to import visualization libraries
visualization_available = False
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    visualization_available = True
except ImportError:
    print(
        '\n*** WARNING: libraries matplotlib and/or seaborn are not installed.\n*** Visualization will not be available!\n'
    )


def show_usage():
    print(
        'Usage: poetry run python summarize_results.py <path_to_output_jsonl_file> <model_name>'
    )
    print(
        'Example:\npoetry run python summarize_results.py evaluation/evaluation_outputs/outputs/AiderBench/CodeActAgent/claude-3-5-sonnet@20240620_maxiter_30_N_v1.9/output.jsonl claude-3-5-sonnet@20240620\n'
    )


def print_error(message: str):
    print(f'\n***\n*** ERROR: {message}\n***\n')
    show_usage()


def extract_test_results(res_file_path: str) -> tuple[list[str], list[str]]:
    passed = []
    failed = []
    with open(res_file_path, 'r') as file:
        for line in file:
            data = json.loads(line.strip())
            instance_id = data['instance_id']
            resolved = False
            if 'test_result' in data and 'exit_code' in data['test_result']:
                resolved = data['test_result']['exit_code'] == 0
            if resolved:
                passed.append(instance_id)
            else:
                failed.append(instance_id)
    return passed, failed


def visualize_results(json_file_path: str, model: str, output_dir: str):
    # based on a Colab notebook by RajMaheshwari
    with open(json_file_path, 'r') as f:
        data = [json.loads(line) for line in f]

    df = pd.DataFrame.from_records(data)

    df1 = pd.DataFrame()
    df1['cost'] = df['metrics'].apply(pd.Series)['accumulated_cost']
    df1['result'] = (
        df['test_result'].apply(pd.Series)['exit_code'].map({0: 'Pass', 1: 'Fail'})
    )
    df1['actions'] = pd.Series([len(a) - 1 for a in df['history']])

    passed = np.sum(df1['result'] == 'Pass')
    total = df.shape[0]
    resolve_rate = round((passed / total) * 100, 2)

    print('Number of passed tests:', f'{passed}/{total}')

    if not visualization_available:
        return resolve_rate

    # Cost histogram
    plt.figure(figsize=(10, 6))
    bins = 10
    mx = pd.Series.max(df1['cost'])
    g = sns.histplot(df1, x='cost', bins=bins, hue='result', multiple='stack')
    x_ticks = np.around(np.linspace(0, mx, bins + 1), 3)
    g.set_xticks(x_ticks)
    g.set_xlabel('Cost in $')
    g.set_title(f'MODEL: {model}, RESOLVE_RATE: {resolve_rate}%', size=9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'cost_histogram.png'))
    plt.close()

    # Actions histogram
    plt.figure(figsize=(10, 6))
    bins = np.arange(0, 31, 2)
    g = sns.histplot(df1, x='actions', bins=bins, hue='result', multiple='stack')
    g.set_xticks(bins)
    g.set_xlabel('# of actions')
    g.set_title(f'MODEL: {model}, RESOLVE_RATE: {resolve_rate}%', size=9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'actions_histogram.png'))
    plt.close()

    return resolve_rate


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print_error('Argument(s) missing!')
        sys.exit(1)

    json_file_path = sys.argv[1]
    model_name = sys.argv[2]

    if not os.path.exists(json_file_path):
        print_error('Output file does not exist!')
        sys.exit(1)
    if not os.path.isfile(json_file_path):
        print_error('Path-to-output-file is not a file!')
        sys.exit(1)

    output_dir = os.path.dirname(json_file_path)
    if not os.access(output_dir, os.W_OK):
        print_error('Output folder is not writable!')
        sys.exit(1)

    passed_tests, failed_tests = extract_test_results(json_file_path)
    resolve_rate = visualize_results(json_file_path, model_name, output_dir)

    print(
        f'\nPassed {len(passed_tests)} tests, failed {len(failed_tests)} tests, resolve rate = {resolve_rate:.2f}%'
    )
    print('PASSED TESTS:')
    print(passed_tests)
    print('FAILED TESTS:')
    print(failed_tests)
    print(
        '\nVisualization results were saved as cost_histogram.png and actions_histogram.png'
    )
    print('in folder: ', output_dir)
