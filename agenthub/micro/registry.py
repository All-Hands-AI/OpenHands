import os

import yaml

all_microagents = {}

for dir in os.listdir(os.path.dirname(__file__)):
    base = os.path.dirname(__file__) + '/' + dir
    if os.path.isfile(base):
        continue
    if dir.startswith('_'):
        continue
    promptFile = base + '/prompt.md'
    agentFile = base + '/agent.yaml'
    if not os.path.isfile(promptFile) or not os.path.isfile(agentFile):
        raise Exception(f'Missing prompt or agent file in {base}. Please create them.')
    with open(promptFile, 'r') as f:
        prompt = f.read()
    with open(agentFile, 'r') as f:
        agent = yaml.safe_load(f)
    if 'name' not in agent:
        raise Exception(f'Missing name in {agentFile}')
    agent['prompt'] = prompt
    all_microagents[agent['name']] = agent
