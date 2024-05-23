import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Get agent's gaia score")
    parser.add_argument('--file', type=str, help="Path to the agent's output.jsonl")
    args = parser.parse_args()
    this_log = args.file
    print(f'Reading {this_log}')
    outs = []
    with open(this_log, 'r') as f:
        lines = f.readlines()
        for line in lines:
            outs.append(json.loads(line))

    total = 0
    success = 0
    for out in outs:
        total += 1
        if out['test_result']:
            success += 1
    print(f'Success rate: {success}/{total} = {success/total}')


if __name__ == '__main__':
    main()
