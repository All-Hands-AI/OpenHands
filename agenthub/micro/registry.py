import os

import yaml

all_microagents = {}

for dir in os.listdir(os.path.dirname(__file__)):
    base = os.path.dirname(__file__) + '/' + dir
    if os.path.isfile(base):
        continue
    if dir.startswith('_'):
        continue
    agentFile = base + '/agent.yaml'
    if not os.path.isfile(agentFile):
        raise Exception(f'Missing prompt or agent file in {base}. Please create them.')
    with open(agentFile, 'r') as f:
        agent = yaml.safe_load(f)
    if 'name' not in agent:
        raise Exception(f'Missing name in {agentFile}')

    prompt = ''
    promptFile = base + '/prompt.md'
    try:
        with open(promptFile, 'r') as f:
            prompt = f.read()
    except FileNotFoundError:
        pass

    agent['prompt'] = prompt
    all_microagents[agent['name']] = agent
