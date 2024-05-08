import os

import yaml

all_microagents: dict = {}


def register_agent(name, agent):
    if 'subagents' in agent:
        for subagent in agent['subagents']:
            sub_name = name + '_' + subagent['name']
            subagent['name'] = sub_name
            register_agent(sub_name, subagent)

    if 'prompt' in agent:
        if agent['prompt'].endswith('.md'):
            with open(base + '/' + agent['prompt'], 'r') as f:
                agent['prompt'] = f.read()

    if 'workflow' in agent:
        for step in agent['workflow']:
            if 'do' not in step:
                raise Exception(f'Missing do for some workflow step in {agentFile}')
            do = step['do']
            if 'action' not in do:
                raise Exception(f'Missing action for some workflow step in {agentFile}')

    all_microagents[name] = agent


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
    register_agent(agent['name'], agent)
