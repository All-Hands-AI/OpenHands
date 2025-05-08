#!/usr/bin/env python3
import argparse
import glob
import json
import os
import random
from collections import Counter

import numpy as np
import pandas as pd

from openhands.events.serialization import event_from_dict
from openhands.events.utils import get_pairs_from_events

ERROR_KEYWORDS = [
    'Agent encountered an error while processing the last action',
    'APIError',
    'Action execution failed',
    'litellm.Timeout: APITimeoutError',
]


def get_bootstrap_accuracy_error_bars(
    values: float | int | bool, num_samples: int = 1000, p_value=0.05
) -> tuple[float, float]:
    sorted_vals = np.sort(
        [np.mean(random.sample(values, len(values) // 2)) for _ in range(num_samples)]
    )
    bottom_idx = int(num_samples * p_value / 2)
    top_idx = int(num_samples * (1.0 - p_value / 2))
    return (sorted_vals[bottom_idx], sorted_vals[top_idx])


def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    num_lines = len(lines)
    num_error_lines = 0
    num_agent_stuck_in_loop = 0
    num_resolved = 0
    resolved_arr = []
    num_empty_patch = 0
    num_unfinished_runs = 0
    error_counter = Counter()
    main_agent_cost = []
    editor_cost = []
    num_turns = []

    for line in lines:
        _d = json.loads(line)

        if 'metrics' not in _d or _d['metrics'] is None:
            # this is a failed run
            num_unfinished_runs += 1
            continue

        # Cost
        costs = _d['metrics'].get('costs', [])
        _cur_main_agent_cost = 0
        _cur_editor_cost = 0
        for cost in costs:
            if isinstance(cost, float):
                # backward compatible
                _cur_main_agent_cost += cost
            else:
                if 'draft_editor' in cost['model']:
                    _cur_editor_cost += cost['cost']
                else:
                    _cur_main_agent_cost += cost['cost']

        main_agent_cost.append(_cur_main_agent_cost)
        editor_cost.append(_cur_editor_cost)

        # Turn status
        history = _d.get('history', [])
        events = [event_from_dict(event) for event in history]
        pairs = get_pairs_from_events(events)
        num_turns.append(len(pairs))

        # Patch & resolve status
        patch = _d.get('test_result', {}).get('git_patch', '')
        if patch == '':
            num_empty_patch += 1
            continue

        report = _d.get('report', {}) or {}
        resolved = report.get('resolved', False)
        if resolved:
            num_resolved += 1
            resolved_arr.append(1)
        else:
            resolved_arr.append(0)

        # Error
        error = _d.get('error', None)

        if error is not None and isinstance(error, str):
            agent_stuck_in_loop = 'Agent got stuck in a loop' in error
            contains_error = bool(error) and not agent_stuck_in_loop
            if agent_stuck_in_loop:
                error_counter['Agent got stuck in a loop'] += 1
                num_agent_stuck_in_loop += 1
            elif contains_error:
                error_counter[error] += 1
            continue

        for keyword in ERROR_KEYWORDS:
            if keyword in line:
                error_counter[keyword] += 1
                num_error_lines += 1
                break

    return {
        'file_path': file_path,
        'total_instances': num_lines,
        'resolved': {
            'count': num_resolved,
            'percentage': (num_resolved / num_lines * 100) if num_lines > 0 else 0,
            'ci': tuple(
                x * 100 for x in get_bootstrap_accuracy_error_bars(resolved_arr)
            ),
        },
        'empty_patches': {
            'count': num_empty_patch,
            'percentage': (num_empty_patch / num_lines * 100) if num_lines > 0 else 0,
        },
        'unfinished_runs': {
            'count': num_unfinished_runs,
            'percentage': (num_unfinished_runs / num_lines * 100)
            if num_lines > 0
            else 0,
        },
        'errors': {
            'total': num_error_lines,
            'percentage': (num_error_lines / num_lines * 100) if num_lines > 0 else 0,
            'stuck_in_loop': {
                'count': num_agent_stuck_in_loop,
                'percentage': (num_agent_stuck_in_loop / num_lines * 100)
                if num_lines > 0
                else 0,
            },
            'breakdown': {
                str(error): {
                    'count': count,
                    'percentage': (count / num_lines * 100) if num_lines > 0 else 0,
                }
                for error, count in error_counter.items()
            },
        },
        'costs': {
            'main_agent': sum(main_agent_cost),
            'editor': sum(editor_cost),
            'total': sum(main_agent_cost) + sum(editor_cost),
        },
        'statistics': {
            'avg_turns': sum(num_turns) / num_lines if num_lines > 0 else 0,
            'costs': {
                'main_agent': sum(main_agent_cost) / num_lines if num_lines > 0 else 0,
                'editor': sum(editor_cost) / num_lines if num_lines > 0 else 0,
                'total': (sum(main_agent_cost) + sum(editor_cost)) / num_lines
                if num_lines > 0
                else 0,
            },
        },
    }


def aggregate_directory(input_path) -> pd.DataFrame:
    # Process all output.jsonl files in subdirectories
    pattern = os.path.join(input_path, '**/output.jsonl')
    files = glob.glob(pattern, recursive=True)
    print(f'Processing {len(files)} files from directory {input_path}')

    # Process each file silently and collect results
    results = []
    for file_path in files:
        try:
            result = process_file(file_path)
            results.append(result)
        except Exception as e:
            print(f'Error processing {file_path}: {str(e)}')
            import traceback

            traceback.print_exc()
            continue

    # Convert results to pandas DataFrame and sort by resolve rate
    df = pd.DataFrame(results)

    # Extract directory name from file path
    df['directory'] = df['file_path'].apply(
        lambda x: os.path.basename(os.path.dirname(x))
    )

    df['resolve_rate'] = df['resolved'].apply(lambda x: x['percentage'])
    df['resolve_rate_ci'] = df['resolved'].apply(lambda x: x['ci'])
    df['empty_patch_rate'] = df['empty_patches'].apply(lambda x: x['percentage'])
    df['unfinished_rate'] = df['unfinished_runs'].apply(lambda x: x['percentage'])
    df['avg_turns'] = df['statistics'].apply(lambda x: x['avg_turns'])
    df['error_rate'] = df['errors'].apply(lambda x: x['percentage'])
    df['avg_cost'] = df['statistics'].apply(lambda x: x['costs']['total'])

    df = df.sort_values('resolve_rate', ascending=False)

    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_path', type=str, help='The file or directory to summarize'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSONL file for results',
        default='summary_results.jsonl',
    )
    args = parser.parse_args()

    if os.path.isdir(args.input_path):
        df = aggregate_directory(args.input_path)
        # Create the summary string
        columns = [
            'directory',
            'resolve_rate',
            'empty_patch_rate',
            'unfinished_rate',
            'error_rate',
            'avg_turns',
            'avg_cost',
            'total_instances',
        ]
        summary_str = df[columns].to_string(
            float_format=lambda x: '{:.2f}'.format(x),
            formatters={
                'directory': lambda x: x[:90]
            },  # Truncate directory names to 20 chars
            index=False,
        )

        # Print to console
        print('\nResults summary (sorted by resolve rate):')
        print(summary_str)

        # Save to text file
        txt_output = args.output.rsplit('.', 1)[0] + '.txt'
        with open(txt_output, 'w') as f:
            f.write('Results summary (sorted by resolve rate):\n')
            f.write(summary_str)

        # Save
        df.to_json(args.output, lines=True, orient='records')
        df[columns].to_csv(args.output.rsplit('.', 1)[0] + '.csv', index=False)
    else:
        # Process single file with detailed output
        results = []
        try:
            result = process_file(args.input_path)
            results.append(result)

            # Print detailed results for single file
            print(f'\nResults for {args.input_path}:')
            print(
                f'Number of resolved: {result["resolved"]["count"]} / {result["total_instances"]} ({result["resolved"]["percentage"]:.2f}% [{result["resolved"]["ci"][0]:.2f}%, {result["resolved"]["ci"][1]:.2f}%])'
            )
            print(
                f'Number of empty patch: {result["empty_patches"]["count"]} / {result["total_instances"]} ({result["empty_patches"]["percentage"]:.2f}%)'
            )
            print(
                f'Number of error lines: {result["errors"]["total"]} / {result["total_instances"]} ({result["errors"]["percentage"]:.2f}%)'
            )
            print(
                f'Number of agent stuck in loop: {result["errors"]["stuck_in_loop"]["count"]} / {result["total_instances"]} ({result["errors"]["stuck_in_loop"]["percentage"]:.2f}%)'
            )
            print(
                f'Number of unfinished runs: {result["unfinished_runs"]["count"]} / {result["total_instances"]} ({result["unfinished_runs"]["percentage"]:.2f}%)'
            )
            print(f'Total cost: {result["costs"]["total"]:.2f} USD')
            print('## Statistics')
            print(
                f'Avg. num of turns per instance: {result["statistics"]["avg_turns"]:.2f}'
            )
            print(
                f'Avg. agent cost per instance: {result["statistics"]["costs"]["main_agent"]:.2f} USD'
            )
            print(
                f'Avg. editor cost per instance: {result["statistics"]["costs"]["editor"]:.2f} USD'
            )
            print(
                f'Avg. total cost per instance: {result["statistics"]["costs"]["total"]:.2f} USD'
            )

            print('## Detailed error breakdown:')
            for error, data in result['errors']['breakdown'].items():
                print(f'{error}: {data["count"]} ({data["percentage"]:.2f}%)')

        except Exception as e:
            print(f'Error processing {args.input_path}: {str(e)}')
