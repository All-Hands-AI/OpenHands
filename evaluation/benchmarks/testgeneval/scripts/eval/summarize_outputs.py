#!/usr/bin/env python3
import argparse
import json
from collections import Counter

from openhands.events.serialization import event_from_dict
from openhands.events.utils import get_pairs_from_events

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

    coverage = 0
    mutation_score = 0
    num_empty_suite = 0

    error_counter = Counter()

    main_agent_cost = []
    editor_cost = []
    num_turns = []

    for line in lines:
        _d = json.loads(line)

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

        # Suite & resolve status
        suite = _d.get('test_result', {}).get('test_suite', '')
        if suite == '':
            num_empty_suite += 1
            continue

        report = _d.get('report', {}) or {}
        coverage += report.get('coverage', 0)
        mutation_score += report.get('mutation_score', 0)

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

    # print the error counter (with percentage)
    print(f'Average coverage for {num_lines} ({coverage / num_lines * 100:.2f}%)')
    print(
        f'Average mutation score for {num_lines} ({mutation_score / num_lines * 100:.2f}%)'
    )

    print(
        f'Number of empty suite: {num_empty_suite} / {num_lines} ({num_empty_suite / num_lines * 100:.2f}%)'
    )
    print(
        f'Number of error lines: {num_error_lines} / {num_lines} ({num_error_lines / num_lines * 100:.2f}%)'
    )
    print(
        f'Number of agent stuck in loop: {num_agent_stuck_in_loop} / {num_lines} ({num_agent_stuck_in_loop / num_lines * 100:.2f}%)'
    )
    assert len(num_turns) == num_lines
    assert len(main_agent_cost) == num_lines
    assert len(editor_cost) == num_lines
    print('## Statistics')
    print(f'Avg. num of turns per instance: {sum(num_turns) / num_lines:.2f}')
    print(f'Avg. agent cost per instance: {sum(main_agent_cost) / num_lines:.2f} USD')
    print(f'Avg. editor cost per instance: {sum(editor_cost) / num_lines:.2f} USD')
    print(
        f'Avg. total cost per instance: {(sum(main_agent_cost) + sum(editor_cost)) / num_lines:.2f} USD'
    )

    print('## Detailed error breakdown:')
    for error, count in error_counter.items():
        print(f'{error}: {count} ({count / num_lines * 100:.2f}%)')
