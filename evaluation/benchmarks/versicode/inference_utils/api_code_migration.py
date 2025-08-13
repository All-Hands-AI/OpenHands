"""GPT performs line level generation prediction and truncates overly long tokens."""

import json
import os

import tiktoken
from openai import OpenAI

max_tokens = 127000  # gpt3.5 is 16ktoken    gpt4o is 128k
model_name = ''

os.environ['OPENAI_API_KEY'] = ''
client = OpenAI()


def truncate_text(text, max_tokens):
    encoding = tiktoken.get_encoding('cl100k_base')
    disallowed_special = ()

    tokens = encoding.encode(text, disallowed_special=disallowed_special)
    print(len(tokens))

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]

    truncated_text = encoding.decode(tokens)

    return truncated_text


def predict(content, model_name):
    response = client.chat.completions.create(
        model=model_name,
        messages=[{'role': 'user', 'content': content}],
        frequency_penalty=0.1,
        max_tokens=128,
        logit_bias=None,
        logprobs=None,
        n=6,
        presence_penalty=0.0,
        seed=None,
        stop=None,
        stream=False,
        temperature=0.8,
        top_p=0.95,
    )
    ans_list = []
    choices_list = response.choices
    for c in choices_list:
        content = c.message.content
        ans_list.append(content)
    final_ans = str(ans_list)
    return final_ans


def bulid_prompt(description, old_version, old_code, new_version) -> str:
    """Build prompt
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
data_dict = lodict
data_list = data_dict


for data in data_list:
    if 'model_output' in data:
        print(
            f'the {data_list.index(data) + 1} has already been predicted, skipping this data!'
        )
        continue
    try:
        print(f'Predicting {data_list.index(data) + 1} ')
        old_version = data['dependency'] + data['old_version']  # package == x.x.x
        new_version = data['dependency'] + data['new_version']  # package == x.x.x
        description = data['description']  # 功能描述
        old_code = data['old_code']  # mask后的代码

        instruction = bulid_prompt(description, old_version, old_code, new_version)
        truncated_text = truncate_text(instruction, max_tokens)
        prediction = predict(truncated_text, model_name)

        data['model_output'] = prediction
    except Exception as e:
        print(f'error：{e}')
        print('save current data')
        save_folder_path = os.path.join(
            '../data/result_data/code_migration', model_name
        )
        if not os.path.exists(save_folder_path):
            os.makedirs(save_folder_path)
        save_json_path = os.path.join(save_folder_path, json_path.split('/')[-1])

        with open(save_json_path, 'w', encoding='utf-8') as fw:
            json.dump(data_dict, fw, indent=4, ensure_ascii=False)
        break


save_folder_path = os.path.join('../data/result_data/code_migration', model_name)
if not os.path.exists(save_folder_path):
    os.makedirs(save_folder_path)
save_json_path = os.path.join(save_folder_path, json_path.split('/')[-1])

with open(save_json_path, 'w', encoding='utf-8') as fw:
    json.dump(data_dict, fw, indent=4, ensure_ascii=False)
