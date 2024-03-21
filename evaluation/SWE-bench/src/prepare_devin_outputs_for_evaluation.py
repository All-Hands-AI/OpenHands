'''
Script used to convert devin's output into the desired json format for evaluation on SWE-bench

Usage:
    python prepare_devin_outputs_for_evaluation.py

Outputs:
    two json files under evaluation/SWE-bench/data/

'''

import requests
import os
from tqdm import tqdm
import json

#fetch devin's outputs into a json file for evaluation
def get_devin_eval_output():
    repo_url = "CognitionAI/devin-swebench-results"
    folder_path = "output_diffs"

    base_url = "https://api.github.com/repos/"
    pass_api_url = f"{base_url}{repo_url}/contents/{folder_path}/pass"
    failed_api_url = f"{base_url}{repo_url}/contents/{folder_path}/fail"

    pass_files_info = []
    failed_files_info = []

    def get_files(api_url, subfolder_name, files_info):
        response = requests.get(api_url)
        if response.status_code == 200:
            contents = response.json()
            for item in tqdm(contents):
                if item["type"] == "file":
                    file_url = f"https://raw.githubusercontent.com/{repo_url}/main/{folder_path}/{subfolder_name}/{item['name']}"
                    file_content = requests.get(file_url).text
                    instance_id = item['name'][:-9]
                    model_name = "Devin"  # Update with actual model name
                    files_info.append({
                        "instance_id": instance_id,
                        "model_patch": file_content,
                        "model_name_or_path": model_name
                    })

    get_files(pass_api_url, "pass", pass_files_info)
    get_files(failed_api_url, "fail", failed_files_info)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "../data/devin/")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(os.path.join(output_dir, "pass_output.json"), "w") as pass_file:
        json.dump(pass_files_info, pass_file, indent=4)

    with open(os.path.join(output_dir, "fail_output.json"), "w") as fail_file:
        json.dump(failed_files_info, fail_file, indent=4)


if __name__ == '__main__':
    get_devin_eval_output()