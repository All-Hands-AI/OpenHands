from .micro.agent import MicroAgent
from opendevin.agent import Agent
import os
import yaml

from dotenv import load_dotenv
load_dotenv()


# Import agents after environment variables are loaded
from . import monologue_agent  # noqa: E402
from . import codeact_agent  # noqa: E402
from . import planner_agent  # noqa: E402
from . import SWE_agent      # noqa: E402

__all__ = ['monologue_agent', 'codeact_agent',
           'planner_agent', 'SWE_agent']

# list all dirs in ./micro
for dir in os.listdir(os.path.dirname(__file__) + '/micro'):
    base = os.path.dirname(__file__) + '/micro/' + dir
    if os.path.isfile(base):
        continue
    if dir.startswith('_'):
        continue
    promptFile = base + '/prompt.md'
    agentFile = base + '/agent.yaml'
    if not os.path.isfile(promptFile) or not os.path.isfile(agentFile):
        raise Exception(
            f'Missing prompt or agent file in {base}. Please create them.')
    with open(promptFile, 'r') as f:
        prompt = f.read()
    with open(agentFile, 'r') as f:
        agent = yaml.safe_load(f)

    anon_class = type(agent['name'], (MicroAgent,), {
        'prompt': prompt,
        'agentDefinition': agent,
    })

    Agent.register(agent['name'], anon_class)
