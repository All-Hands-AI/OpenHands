"""
token completion
"""
import copy
import json
import os
from vllm import LLM, SamplingParams
import tiktoken
import time
import gc
import torch
from multiprocessing import Process

# os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

def truncate_text(text, max_tokens):
    encoding = tiktoken.get_encoding("cl100k_base")
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
        version = data['dependency'] + data['version']  # package == x.x.x
        description = data['description']  # func description
        masked_code = data['masked_code']  # masked code

        instruction = bulid_prompt(version, description, masked_code)
        test_list.append(instruction)

    sampling_params = SamplingParams(n=100, temperature=0.8, top_p=0.95, max_tokens=64)
    llm = LLM(model=model_name, tensor_parallel_size=4, gpu_memory_utilization=0.9, swap_space=20)

    outputs = llm.generate(test_list, sampling_params)
    for output in outputs:
        requests_id = int(output.request_id)
        temp_ans_list = []
        output_list = output.outputs
        for o in output_list:
            text = o.text
            temp_ans_list.append(text)

        temp_data_list[requests_id]['model_output'] = str(temp_ans_list)

    save_folder_path = os.path.join('../data/result_data/token_completion', model_name.split('/')[-1])
    if not os.path.exists(save_folder_path):
        os.makedirs(save_folder_path)

    save_json_path = os.path.join(save_folder_path, json_path.split('/')[-1])

    with open(save_json_path, 'w', encoding='utf-8') as fw:
        json.dump({'count': len(temp_data_list), 'data': temp_data_list}, fw, indent=4, ensure_ascii=False)

    gc.collect()
    torch.cuda.empty_cache()

def bulid_prompt(version, description, masked_code) -> str:
    """
    build prompt
    :param version:
    :param description:
    :param masked_code:
    :param options:
    :return:
    """
    prompt = f"""
        You are a professional Python programming engineer, and I will give you a code snippet where function names are masked and represented as<mask>in the code. 
        There may be multiple <mask>, and all the blocked content in these <mask> is the same. 
        I will provide a functional description of this code, the dependency package to which the function belongs and the version of the dependency package.
        What you need to do is infer what the masked function name is based on this information. You only need to return one content, not every<mask>.
        Please note that you only need to return one function name and do not need to return any other redundant content, and the response is enclosed by <start> and <end> Here is an example:
        ###code snippet：
        outputs = llm.<mask>(prompts, sampling_params)
        ###Function Description：
        This code passes prompts and parameters to the model to obtain the output result of the model.
        ###dependeny and version：
        vllm==0.3.3
        ###response：
        <start>generate<end>

        ###code snippet：
        {masked_code}
        ###Function Description：
        {description}
        ###dependeny and version：
        {version}
        ###response：
        """

    return prompt

json_path = '../data/test_data/VersiCode_token_completion.json'

with open(json_path, 'r', encoding='utf-8')as fr:
    lodict = json.load(fr)

origin_data_list = lodict['data']

for model_name in model_list:
    process = Process(target=run_inference, args=(model_name, origin_data_list))
    process.start()
    process.join()
    time.sleep(120)

