import json
import os
import re
import string
import zipfile

import requests


def download_data(dir):
    import gdown

    data_path = os.path.join(dir, 'data/external_corpus')
    if os.path.exists(data_path):
        return data_path
    url = 'https://drive.google.com/uc?id=1zRbHzPW2x4dDcfmphBWlan8cxUCRNmqk'
    zip_path = os.path.join(dir, 'data.zip')
    gdown.download(url, zip_path, quiet=False)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.path.join(dir, 'data'))
    if os.path.exists(zip_path):
        os.remove(zip_path)
    print(f'Data saved to {data_path}')
    return data_path


def download_tools(dir, wolfram_alpha_appid='YOUR_WOLFRAMALPHA_APPID'):
    tool_path = os.path.join(dir, 'tools')
    if os.path.exists(tool_path):
        return tool_path
    os.mkdir(tool_path)
    tools = [
        'code/sql_interpreter.py',
        'graph/graphtools.py',
        'math/calculator.py',
        'table/mysql_db_create.py',
        'table/tabtools.py',
        'text/agenda_retriever.py',
        'text/scirex_retriever.py',
    ]
    for tool in tools:
        url = f'https://raw.githubusercontent.com/night-chen/ToolQA/main/benchmark/ReAct/code/tools/{tool}'
        response = requests.get(url)
        output_file = os.path.join(tool_path, tool.split('/')[1])
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f'Tool saved to {output_file}')
    with open(os.path.join(tool_path, 'calculator.py'), 'r') as f:
        content = f.read()
    new_content = content.replace('YOUR_WOLFRAMALPHA_APPID', wolfram_alpha_appid)
    with open(os.path.join(tool_path, 'calculator.py'), 'w') as f:
        f.write(new_content)
    with open(os.path.join(tool_path, 'agenda_retriever.py'), 'r') as f:
        content = f.read()
    new_content = content.replace('/<YOUR_OWN_PATH>/ToolQA/', '')
    with open(os.path.join(tool_path, 'agenda_retriever.py'), 'w') as f:
        f.write(new_content)
    with open(os.path.join(tool_path, 'mysql_db_create.py'), 'r') as f:
        content = f.read()
    new_content = content.replace('/<YOUR_OWN_PATH>/ToolQA/', '')
    with open(os.path.join(tool_path, 'mysql_db_create.py'), 'w') as f:
        f.write(new_content)
    with open(os.path.join(tool_path, 'scirex_retriever.py'), 'r') as f:
        content = f.read()
    new_content = content.replace('/<YOUR_OWN_PATH>/ToolQA/', '')
    with open(os.path.join(tool_path, 'scirex_retriever.py'), 'w') as f:
        f.write(new_content)


LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def get_data(dataset, hardness):
    data_path = os.path.join(LOCAL_DATA_DIR, f'{dataset}-{hardness}.jsonl')
    if os.path.exists(data_path):
        print(f'Loading data from {data_path}')
        with open(data_path, 'r') as f:
            return json.load(f)
    else:
        print(
            f'Downloading data from https://raw.githubusercontent.com/night-chen/ToolQA/main/data/questions/{hardness}/{dataset}-{hardness}.jsonl'
        )
        data = []
        url = f'https://raw.githubusercontent.com/night-chen/ToolQA/main/data/questions/{hardness}/{dataset}-{hardness}.jsonl'
        url = requests.get(url)
        if url.status_code == 200:
            lines = url.text.splitlines()
            for line in lines:
                data.append(json.loads(line))
            with open(data_path, 'w') as f:
                json.dump(data, f)
        print(f'Data saved to {data_path}')
    return data


REACT_INSTRUCTION = """Use tools in the tools directory to solve the task: {question}
You could use all tools which are under the tools/ directory and all the data under the data/ directory.
When you think you finished the task, respond with `Finish[answer]` where you include your answer in `[]`.
IMPORTANT: Make sure that in your final answer, you should not print any additional text/instructions other than the actual answer, which should be a word or a simple phrase.
"""


def encode_question(question):
    return REACT_INSTRUCTION.format(question=question)


# imported from https://github.com/night-chen/ToolQA/tree/main/benchmark/ReAct/code/agents_chatgpt.py
def normalize_answer(s):
    def remove_articles(text):
        return re.sub(r'\b(a|an|the|usd)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def eval_answer(pred, answer):
    pattern = r'Finish\[(.*?)\]'
    match = re.search(pattern, pred)
    if match:
        pred = match.group(1)
    return normalize_answer(pred) == normalize_answer(answer)
