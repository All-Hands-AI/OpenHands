import argparse
import json
import requests
from functools import partial
import sys
import gdown
import zipfile
import os
import re
import string

def download_data(dir):
    data_path = os.path.join(dir, "data/external_corpus")
    if os.path.exists(data_path): return data_path
    url = "https://drive.google.com/uc?id=1zRbHzPW2x4dDcfmphBWlan8cxUCRNmqk"
    zip_path = os.path.join(dir, "data.zip")
    gdown.download(url, zip_path, quiet=False)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.path.join(dir, "data"))
    if os.path.exists(zip_path): os.remove(zip_path)
    return data_path

def download_tools(dir, wolfram_alpha_appid = "YOUR_WOLFRAMALPHA_APPID"):
    tool_path = os.path.join(dir, "tools")
    if os.path.exists(tool_path): return tool_path
    os.mkdir(tool_path)
    tools = ["code/sql_interpreter.py", "graph/graphtools.py", "math/calculator.py", "table/mysql_db_create.py", "table/tabtools.py", "text/agenda_retriever.py", "text/scirex_retriever.py"]
    for tool in tools:
        url = f"https://raw.githubusercontent.com/night-chen/ToolQA/main/benchmark/ReAct/code/tools/{tool}"
        response = requests.get(url)
        output_file = os.path.join(tool_path, tool.split("/")[1])
        with open(output_file, 'wb') as f:
            f.write(response.content)
    with open(os.path.join(tool_path, "calculator.py"), "r") as f:
        content = f.read()
    new_content = content.replace("YOUR_WOLFRAMALPHA_APPID", wolfram_alpha_appid)
    with open(os.path.join(tool_path, "calculator.py"), "w") as f:
        f.write(new_content)
    with open(os.path.join(tool_path, "agenda_retriever.py"), "r") as f:
        content = f.read()
    new_content = content.replace("/<YOUR_OWN_PATH>/ToolQA/", "")
    with open(os.path.join(tool_path, "agenda_retriever.py"), "w") as f:
        f.write(new_content)
    with open(os.path.join(tool_path, "mysql_db_create.py"), "r") as f:
        content = f.read()
    new_content = content.replace("/<YOUR_OWN_PATH>/ToolQA/", "")
    with open(os.path.join(tool_path, "mysql_db_create.py"), "w") as f:
        f.write(new_content)
    with open(os.path.join(tool_path, "scirex_retriever.py"), "r") as f:
        content = f.read()
    new_content = content.replace("/<YOUR_OWN_PATH>/ToolQA/", "")
    with open(os.path.join(tool_path, "scirex_retriever.py"), "w") as f:
        f.write(new_content)

def get_data(dataset, hardness):
    data = []
    url = f"https://raw.githubusercontent.com/night-chen/ToolQA/main/data/questions/{hardness}/{dataset}-{hardness}.jsonl"
    url = requests.get(url)
    if url.status_code == 200:
        lines = url.text.splitlines()
        for line in lines:
            data.append(json.loads(line))
    return data

REACT_INSTRUCTION = """Solve a question answering task. You could use all tools which are under the tools/ directory and all the data under the data/ directory. Below is a detailed explanation of the tools under the tools/ directory.
(1) calculator.WolframAlphaCalculator, which calculates the input formula and returns the result. You could use this tool by `from tools.calculator import WolframAlphaCalculator`.
(2) agenda_retriever.query_llm, which retrieves the agenda related to a keyword. You could use this tool by `from tools.agenda_retriever import query_llm`. 
(3) scirex_retriever.query_llm, which retrieves machine learning papers' paragraphs related to keyword. You could use this tool by `from tools.scirex_retriever import query_llm`. 
(4) table_toolkits.db_loader, which loads a database and returns the database. The database can be one of the following: flights/coffee/airbnb/yelp. You could use this tool by `from tools.tabtools import table_toolkits`, then `toolkits = table_toolkits('')`, and then `db_loader = toolkits.db_loader`.
(5) table_toolkits.data_filter, which filters a database by a column using the relation (e.g., =, >, etc.) and a value, and returns the filtered database. You could use this tool by `from tools.tabtools import table_toolkits`, then `toolkits = table_toolkits('')`, and then `data_filter = toolkits.data_filter`.
(6) table_toolkits.get_value, which returns the value of a column in a database. You could use this tool by `from tools.tabtools import table_toolkits`, then `toolkits = table_toolkits('')`, and then `get_value = toolkits.get_value`.
(7) graph_toolkits.load_graph, which loads a graph and returns the graph. The graph can be one of the following: PaperNet/AuthorNet. You could use this tool by `from tools.graphtools import graph_toolkits`, then `toolkits = graph_toolkits('')`, and then `load_graph = toolkits.load_graph`.
(8) graph_toolkits.check_neighbours, which lists the neighbours of a node in a graph and returns the neighbours. You could use this tool by `from tools.graphtools import graph_toolkits`, then `toolkits = graph_toolkits('')`, and then `check_neighbours = toolkits.check_neighbours`.
(9) graph_toolkits.check_nodes, which returns the detailed attribute information of a node. You could use this tool by `from tools.graphtools import graph_toolkits`, then `toolkits = graph_toolkits('')`, and then `check_nodes = toolkits.check_nodes`.
(10) graph_toolkits.check_edges, which returns the detailed attribute information of the edge between two nodes. You could use this tool by `from tools.graphtools import graph_toolkits`, then `toolkits = graph_toolkits('')`, and then `check_edges = toolkits.check_edges`.
(11) sql_interpreter.execute, which interprets an SQL query and returns the result. You could use this tool by `from tools.sql_interpreter import execute`.
(12) exec, which interprets some Python code and returns the result.

You may take as many steps as necessary. When you think you finished the task, respond with `Finish[answer]` where you include your answer in `[]`. 
IMPORTANT: Make sure that in your final answer, you should not print any additional text/instructions other than the actual answer, which should be a word or a simple phrase.
Question: {question}"""

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
        return re.sub(r"\b(a|an|the|usd)\b", " ", text)
    def white_space_fix(text):
        return " ".join(text.split())
    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)
    def lower(text):
        return text.lower()
    return white_space_fix(remove_articles(remove_punc(lower(s))))

def eval_answer(pred, answer):
    pattern = r'Finish\[(.*?)\]'
    match = re.search(pattern, pred)
    if match: pred = match.group(1)
    return normalize_answer(pred) == normalize_answer(answer)

