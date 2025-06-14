"""
code migration
"""

import copy
import gc
import json
import os
import time
from multiprocessing import Process

import tiktoken
import torch
from vllm import LLM, SamplingParams

# os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"


def truncate_text(text, max_tokens):
    encoding = tiktoken.get_encoding('cl100k_base')
    disallowed_special = ()

    tokens = encoding.encode(text, disallowed_special=disallowed_special)
    print(len(tokens))

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]

    truncated_text = encoding.decode(tokens)

    return truncated_text


model_list = ['/data2/base models/starcoder2-15b', '/data2/base models/CodeGemma-7B']


def run_inference(model_name, origin_data_list):
    temp_data_list = copy.deepcopy(origin_data_list)
    test_list = []
    for data in temp_data_list:
        old_version = data['dependency'] + data['old_version']  # package == x.x.x
        new_version = data['dependency'] + data['new_version']  # package == x.x.x
        description = data['description']  # 功能描述
        old_code = data['old_code']  # mask后的代码

        instruction = bulid_prompt(description, old_version, old_code, new_version)
        test_list.append(instruction)

    sampling_params = SamplingParams(n=6, temperature=0.8, top_p=0.95, max_tokens=512)
    llm = LLM(
        model=model_name,
        tensor_parallel_size=4,
        gpu_memory_utilization=0.6,
        swap_space=40,
    )

    outputs = llm.generate(test_list, sampling_params)
    for output in outputs:
        requests_id = int(output.request_id)
        temp_ans_list = []
        output_list = output.outputs
        for o in output_list:
            text = o.text
            temp_ans_list.append(text)

        temp_data_list[requests_id]['model_output'] = str(temp_ans_list)

    save_folder_path = os.path.join(
        '../data/result_data/code_migration', model_name.split('/')[-1]
    )
    if not os.path.exists(save_folder_path):
        os.makedirs(save_folder_path)

    save_json_path = os.path.join(save_folder_path, json_path.split('/')[-1])

    with open(save_json_path, 'w', encoding='utf-8') as fw:
        json.dump(temp_data_list, fw, indent=4, ensure_ascii=False)

    gc.collect()
    torch.cuda.empty_cache()


def bulid_prompt(description, old_version, old_code, new_version) -> str:
    """
    build prompt
    :param version:
    :param description:
    :param masked_code:
    :param options:
    :return:
    """
    prompt = f"""
    You are now a professional Python programming engineer. I will provide you with a code snippet and a description of its functionality,
    including the dependencies and versions used in the code. Then, I will provide the same dependencies but with a specified new version.
    Your task is to refactor the code using the methods provided by the specified new version and return the refactored code.
    Please note that you only need to return the refactored code and enclose it with <start> and <end>:
    ###Functionality description of the code
    {description}
    ###Dependency and old version
    {old_version}
    ###Old version code
    {old_code}
    ###Dependency and new version
    {new_version}
    ###Refactored new code
    """

    return prompt


json_path = '../data/test_data/VersiCode_migration.json'

with open(json_path, 'r', encoding='utf-8') as fr:
    lodict = json.load(fr)

origin_data_list = lodict

for model_name in model_list:
    process = Process(target=run_inference, args=(model_name, origin_data_list))
    process.start()
    process.join()
    time.sleep(120)
