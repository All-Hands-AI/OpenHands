"""
GPT performs line level generation prediction and truncates overly long tokens
"""
import json
import openai
from openai import OpenAI
import os
import tiktoken
max_tokens = 127000   #gpt3.5 is 16ktoken    gpt4o is 128k
model_name = "gpt-4o"

os.environ["OPENAI_API_KEY"] = ""
client = OpenAI()

def truncate_text(text, max_tokens):
    encoding = tiktoken.get_encoding("cl100k_base")
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
        messages=[
            {
                "role": "user",
                "content": content
            }
        ],
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
        top_p=0.95
    )
    ans_list = []
    choices_list = response.choices
    for c in choices_list:
        content = c.message.content
        ans_list.append(content)
    final_ans = str(ans_list)
    return final_ans

def bulid_prompt(version, description, masked_code) -> str:
    """
    build prompt
    :param version:
    :param description:
    :param masked_code:
    :param options:
    :return:
    """
    prompt = f'''
            You will act as a professional Python programming engineer, and I will provide a code snippet where a certain line in the code will be masked and represented as<mask>.
            I will provide a functional description related to this code segment, the dependency packages related to this line of code, and the versions of the dependency packages.
            You need to infer the masked line of code based on this information. Note that you only need to return one line of code, and the line is the response you infer.
            Please be careful not to return the information I provided, only the content of the response needs to be returned Enclose that line of code with tags <start> and <end>. Here is an example:

            ###code snippet：
            for output in outputs:
                prompt = output.prompt
                <mask>
                print("Prompt,Generated text")
            ###Function Description：
            The function of this code is to print the results predicted by calling the model using vllm.
            ###dependeny and version：
            vllm==0.3.3
            ###response:
            <start>generated_text = output.outputs[0].text<end>

            ###code snippet：
            {masked_code}
            ###Function Description：
            {description}
            ###dependeny and version:
            {version}
            ###response:

        '''
    return prompt


json_path = '../data/test_data/VersiCode_line_completion.json'


with open(json_path, 'r', encoding='utf-8')as fr:
    lodict = json.load(fr)
data_dict = lodict
data_list = data_dict['data']


for data in data_list:
    if "model_output" in data:
        print(f"the {data_list.index(data) + 1} has already been predicted, skipping this data!")
        continue
    try:
        print(f"Predicting {data_list.index(data) + 1} ")
        version = data['dependency'] + data['version']  #   package == x.x.x
        description = data['description']   #   function description
        masked_code = data['masked_code']   #   masked code

        instruction = bulid_prompt(version, description, masked_code)
        truncated_text = truncate_text(instruction, max_tokens)
        prediction = predict(truncated_text, model_name)

        data['model_output'] = prediction
    except Exception as e:
        print(f"error：{e}")
        print("save current data")
        save_folder_path = os.path.join('../data/result_data/line_completion', model_name)
        if not os.path.exists(save_folder_path):
            os.makedirs(save_folder_path)
        save_json_path = os.path.join(save_folder_path, json_path.split('/')[-1])

        with open(save_json_path, 'w', encoding='utf-8') as fw:
            json.dump(data_dict, fw, indent=4, ensure_ascii=False)
        break



save_folder_path = os.path.join('../data/result_data/line_completion', model_name)
if not os.path.exists(save_folder_path):
    os.makedirs(save_folder_path)
save_json_path = os.path.join(save_folder_path, json_path.split('/')[-1])

with open(save_json_path, 'w', encoding='utf-8')as fw:
    json.dump(data_dict, fw, indent=4, ensure_ascii=False)



