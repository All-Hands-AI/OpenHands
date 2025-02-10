import argparse
import gzip
import json
import os
from glob import glob

from tqdm import tqdm

tqdm.pandas()


# Load trajectories for resolved instances
def load_completions(output_dir: str, instance_id: str):
    glob_path = os.path.join(output_dir, 'llm_completions', instance_id, '*.json')
    files = sorted(glob(glob_path))  # this is ascending order
    # pick the last file (last turn)
    try:
        file_path = files[-1]
    except IndexError:
        # print(f'No files found for instance {instance_id}: files={files}')
        return None
    with open(file_path, 'r') as f:
        result = json.load(f)
    # create messages
    messages = result['messages']
    messages.append(result['response']['choices'][0]['message'])
    tools = result['kwargs'].get('tools', [])
    return {
        'messages': messages,
        'tools': tools,
    }


parser = argparse.ArgumentParser()
parser.add_argument('jsonl_path', type=str)
args = parser.parse_args()

output_dir = os.path.dirname(args.jsonl_path)
output_path = os.path.join(output_dir, 'output.with_completions.jsonl.gz')

# Check if output would be different from input
needs_update = False
with open(args.jsonl_path, 'r') as f_in:
    for line in tqdm(f_in, desc='Checking for changes'):
        data = json.loads(line)
        new_completions = load_completions(output_dir, data['instance_id'])
        current_completions = data.get('raw_completions')
        if current_completions != new_completions:
            needs_update = True
            break

if not needs_update:
    print('No updates required. Skipping file update.')
    exit(0)

if os.path.exists(output_path):
    print(f'Output file already exists at {output_path}, overwriting? (y/n)')
    if input() != 'y':
        print('Exiting...')
        exit(0)

# Process line by line
with open(args.jsonl_path, 'r') as f_in, gzip.open(output_path, 'wt') as f_out:
    for line in tqdm(f_in):
        data = json.loads(line)
        data['raw_completions'] = load_completions(output_dir, data['instance_id'])
        f_out.write(json.dumps(data) + '\n')

print(f'Saved compressed output to {output_path}')
