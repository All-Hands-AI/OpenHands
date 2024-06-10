import argparse
import json

import pandas as pd
from datasets import load_dataset

parser = argparse.ArgumentParser()
parser.add_argument(
    'output_dir',
    type=str,
    default='eval_data/instances',
    help='Path to the directory to save the instances.',
)
args = parser.parse_args()

dataset = load_dataset('princeton-nlp/SWE-bench')
test = dataset['test'].to_pandas()
test['FAIL_TO_PASS'] = test['FAIL_TO_PASS'].apply(json.loads)
test['PASS_TO_PASS'] = test['PASS_TO_PASS'].apply(json.loads)
test.to_json(f'{args.output_dir}/swe-bench-test.json', orient='records')

dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
test = dataset['test'].to_pandas()
test['FAIL_TO_PASS'] = test['FAIL_TO_PASS'].apply(json.loads)
test['PASS_TO_PASS'] = test['PASS_TO_PASS'].apply(json.loads)
test.to_json(f'{args.output_dir}/swe-bench-lite-test.json', orient='records')

dev = dataset['dev'].to_pandas()
dev['FAIL_TO_PASS'] = dev['FAIL_TO_PASS'].apply(json.loads)
dev['PASS_TO_PASS'] = dev['PASS_TO_PASS'].apply(json.loads)
dev.to_json(f'{args.output_dir}/swe-bench-lite-dev.json', orient='records')

all_data = pd.concat([test, dev])
all_data.to_json(f'{args.output_dir}/swe-bench-lite-all.json', orient='records')
