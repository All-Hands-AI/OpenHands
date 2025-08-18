import argparse
import json


def main(output_jsonl: str):
    with open(output_jsonl, 'r') as f:
        for line in f:
            try:
                output = json.loads(line)
                pred = {
                    'instance_id': output['instance_id'],
                    'model_name_or_path': output['metadata']['llm_config']['model'],
                    'model_patch': output['test_result']['git_patch'],
                }
            except Exception as e:
                print(
                    f'Error while reading output of instance {output["instance_id"]}: {e}'
                )

            print(json.dumps(pred))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output_jsonl',
        type=str,
        required=True,
        help='Path to the prediction file (.../outputs.jsonl)',
    )
    args = parser.parse_args()

    main(args.output_jsonl)
