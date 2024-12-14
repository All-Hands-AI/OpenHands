import json
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'log_fname',
        type=str,
    )
    args = parser.parse_args()

    fname = args.log_fname
    out_fname = args.log_fname.replace('.jsonl', '.converted.jsonl')

    log = [json.loads(line) for line in open(fname)]

    simple_log = [
        json.dumps(
            {
                'instance_id': ex['instance_id'],
                'instruction': ex['instruction'],
                'test_result': ex['test_result'],
                'cost': ex['metrics']['accumulated_cost'],
            }
        )
        for ex in log
    ]

    with open(out_fname, 'w+', encoding='utf-8') as f:
        f.write('\n'.join(simple_log))
