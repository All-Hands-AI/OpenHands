import json
import os
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument("--input_path", type=str, help="Name of input path to JSON file.")
parser.add_argument("--output_path", type=str, help="Name of output path to JSON file.")
args = parser.parse_args()

input_path = args.input_path
output_path = args.output_path
os.makedirs(output_path, exist_ok=True)

def load_jsonl(file_path):  
    """Load JSONL file into a list of dictionaries."""  
    data = []  
    with open(file_path, 'r') as f:  
        for line in f:  
            data.append(json.loads(line))  
    return data 

dataset = load_jsonl(input_path)
ooutput_dataset = []
for data in dataset:
    instance_id = data["instance_id"]
    model_name_or_path = "openhands"
    model_patch = data['test_result']['git_patch'] if 'test_result' in data and 'git_patch' in data['test_result'] else None
    ooutput_dataset.append({
        "instance_id": instance_id,
        "model_name_or_path": model_name_or_path,
        "model_patch": model_patch
    })

with open(os.path.join(output_path, "output.jsonl"), 'w') as f:
    for item in ooutput_dataset:
        json_line = json.dumps(item, ensure_ascii=False)
        f.write(json_line + '\n')