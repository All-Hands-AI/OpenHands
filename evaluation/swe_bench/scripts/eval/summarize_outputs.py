#!/usr/bin/env python3
import argparse
import json
from collections import Counter

ERROR_KEYWORDS = [
    'Agent encountered an error while processing the last action',
    'APIError',
    'Action execution failed',
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_file', type=str, help='The file to summarize')
    args = parser.parse_args()

    with open(args.output_file, 'r') as file:
        lines = file.readlines()

    num_lines = len(lines)
    num_error_lines = 0
    num_agent_stuck_in_loop = 0

    num_resolved = 0
    num_empty_patch = 0

    error_counter = Counter()

    for line in lines:
        _d = json.loads(line)
        patch = _d.get('test_result', {}).get('git_patch', '')
        if patch == '':
            num_empty_patch += 1
            continue

        report = _d.get('report', {}) or {}
        resolved = report.get('resolved', False)
        if resolved:
            num_resolved += 1

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

    # print the error counter (with percentage)
    print('-' * 100)
    print(
        f'# of resolved: {num_resolved} / {num_lines} ({num_resolved / num_lines * 100:.2f}%)'
    )
    print(
        f'# of empty patch: {num_empty_patch} / {num_lines} ({num_empty_patch / num_lines * 100:.2f}%)'
    )
    print(
        f'# of error lines: {num_error_lines} / {num_lines} ({num_error_lines / num_lines * 100:.2f}%)'
    )
    print(
        f'# of loop: {num_agent_stuck_in_loop} / {num_lines} ({num_agent_stuck_in_loop / num_lines * 100:.2f}%)'
    )
    print('-' * 100)
    print('Detailed error breakdown:')
    for error, count in error_counter.items():
        print(f'{error}: {count} ({count / num_lines * 100:.2f}%)')
