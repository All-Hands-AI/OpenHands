import argparse

import pandas as pd
from datasets import load_dataset

parser = argparse.ArgumentParser()
parser.add_argument('output_filepath', type=str, help='Path to save the output file')
parser.add_argument(
    '--dataset_name',
    type=str,
    help='Name of the dataset to download',
    default='princeton-nlp/SWE-bench_Lite',
)
parser.add_argument('--split', type=str, help='Split to download', default='test')
args = parser.parse_args()

dataset = load_dataset(args.dataset_name, split=args.split)
output_filepath = args.output_filepath
print(
    f'Downloading gold patches from {args.dataset_name} (split: {args.split}) to {output_filepath}'
)
patches = [
    {'instance_id': row['instance_id'], 'model_patch': row['patch']} for row in dataset
]
print(f'{len(patches)} gold patches loaded')
pd.DataFrame(patches).to_json(output_filepath, lines=True, orient='records')
print(f'Patches saved to {output_filepath}')
