#!/usr/bin/env python3
"""
Script to aggregate token usage metrics from LLM completion files.

Usage:
    python aggregate_token_usage.py <directory_path> [--input-cost <cost>] [--output-cost <cost>] [--cached-cost <cost>]

Arguments:
    directory_path: Path to the directory containing completion files
    --input-cost: Cost per input token (default: 0.0)
    --output-cost: Cost per output token (default: 0.0)
    --cached-cost: Cost per cached token (default: 0.0)
"""

import argparse
import json
import os
from pathlib import Path


def aggregate_token_usage(
    directory_path, input_cost=0.0, output_cost=0.0, cached_cost=0.0
):
    """
    Aggregate token usage metrics from all JSON completion files in the directory.

    Args:
        directory_path (str): Path to directory containing completion files
        input_cost (float): Cost per input token
        output_cost (float): Cost per output token
        cached_cost (float): Cost per cached token
    """

    # Initialize counters
    totals = {
        'input_tokens': 0,
        'output_tokens': 0,
        'cached_tokens': 0,
        'total_tokens': 0,
        'files_processed': 0,
        'files_with_errors': 0,
        'cost': 0,
    }

    # Find all JSON files recursively
    json_files = list(Path(directory_path).rglob('*.json'))

    print(f'Found {len(json_files)} JSON files to process...')

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Look for usage data in response or fncall_response
            usage_data = None
            if (
                'response' in data
                and isinstance(data['response'], dict)
                and 'usage' in data['response']
            ):
                usage_data = data['response']['usage']
            elif (
                'fncall_response' in data
                and isinstance(data['fncall_response'], dict)
                and 'usage' in data['fncall_response']
            ):
                usage_data = data['fncall_response']['usage']

            if usage_data:
                # Extract token counts
                completion_tokens = usage_data.get('completion_tokens', 0)
                prompt_tokens = usage_data.get('prompt_tokens', 0)
                cached_tokens = usage_data.get('cached_tokens', 0)

                # Handle cases where cached_tokens might be in prompt_tokens_details
                if cached_tokens == 0 and 'prompt_tokens_details' in usage_data:
                    details = usage_data['prompt_tokens_details']
                    if isinstance(details, dict) and 'cached_tokens' in details:
                        cached_tokens = details.get('cached_tokens', 0) or 0

                # Calculate non-cached input tokens
                non_cached_input = prompt_tokens - cached_tokens

                # Update totals
                totals['input_tokens'] += non_cached_input
                totals['output_tokens'] += completion_tokens
                totals['cached_tokens'] += cached_tokens
                totals['total_tokens'] += prompt_tokens + completion_tokens

            if 'cost' in data:
                totals['cost'] += data['cost']
            totals['files_processed'] += 1

            # Progress indicator
            if totals['files_processed'] % 1000 == 0:
                print(f'Processed {totals["files_processed"]} files...')

        except Exception as e:
            totals['files_with_errors'] += 1
            if totals['files_with_errors'] <= 5:  # Only show first 5 errors
                print(f'Error processing {json_file}: {e}')

    # Calculate costs
    input_cost_total = totals['input_tokens'] * input_cost
    output_cost_total = totals['output_tokens'] * output_cost
    cached_cost_total = totals['cached_tokens'] * cached_cost
    total_cost = input_cost_total + output_cost_total + cached_cost_total

    # Print results
    print('\n' + '=' * 60)
    print('TOKEN USAGE AGGREGATION RESULTS')
    print('=' * 60)
    print(f'Files processed: {totals["files_processed"]:,}')
    print(f'Files with errors: {totals["files_with_errors"]:,}')
    print()
    print('TOKEN COUNTS:')
    print(f'  Input tokens (non-cached):             {totals["input_tokens"]:,}')
    print(f'  Output tokens:                         {totals["output_tokens"]:,}')
    print(f'  Cached tokens:                         {totals["cached_tokens"]:,}')
    print(f'  Total tokens:                          {totals["total_tokens"]:,}')
    print(f'  Total costs (based on returned value): ${totals["cost"]:.6f}')
    print()

    if input_cost > 0 or output_cost > 0 or cached_cost > 0:
        print('COST CALCULATED BASED ON PROVIDED RATE:')
        print(
            f'  Input cost:   ${input_cost_total:.6f} ({totals["input_tokens"]:,} × ${input_cost:.6f})'
        )
        print(
            f'  Output cost:  ${output_cost_total:.6f} ({totals["output_tokens"]:,} × ${output_cost:.6f})'
        )
        print(
            f'  Cached cost:  ${cached_cost_total:.6f} ({totals["cached_tokens"]:,} × ${cached_cost:.6f})'
        )
        print(f'  Total cost:   ${total_cost:.6f}')
        print()

    print('SUMMARY:')
    print(
        f'  Total input tokens:  {totals["input_tokens"] + totals["cached_tokens"]:,}'
    )
    print(f'  Total output tokens: {totals["output_tokens"]:,}')
    print(f'  Grand total tokens:  {totals["total_tokens"]:,}')

    return totals


def main():
    parser = argparse.ArgumentParser(
        description='Aggregate token usage metrics from LLM completion files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python aggregate_token_usage.py /path/to/completions
  python aggregate_token_usage.py /path/to/completions --input-cost 0.000001 --output-cost 0.000002
  python aggregate_token_usage.py /path/to/completions --input-cost 0.000001 --output-cost 0.000002 --cached-cost 0.0000005
        """,
    )

    parser.add_argument(
        'directory_path', help='Path to directory containing completion files'
    )

    parser.add_argument(
        '--input-cost',
        type=float,
        default=0.0,
        help='Cost per input token (default: 0.0)',
    )

    parser.add_argument(
        '--output-cost',
        type=float,
        default=0.0,
        help='Cost per output token (default: 0.0)',
    )

    parser.add_argument(
        '--cached-cost',
        type=float,
        default=0.0,
        help='Cost per cached token (default: 0.0)',
    )

    args = parser.parse_args()

    # Validate directory path
    if not os.path.exists(args.directory_path):
        print(f"Error: Directory '{args.directory_path}' does not exist.")
        return 1

    if not os.path.isdir(args.directory_path):
        print(f"Error: '{args.directory_path}' is not a directory.")
        return 1

    # Run aggregation
    try:
        aggregate_token_usage(
            args.directory_path, args.input_cost, args.output_cost, args.cached_cost
        )
        return 0
    except Exception as e:
        print(f'Error during aggregation: {e}')
        return 1


if __name__ == '__main__':
    exit(main())
