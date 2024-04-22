from .micro.registry import all_agents
from .micro.agent import MicroAgent
from opendevin.agent import Agent

from dotenv import load_dotenv
load_dotenv()


# Import agents after environment variables are loaded
from . import monologue_agent  # noqa: E402
from . import codeact_agent  # noqa: E402
from . import planner_agent  # noqa: E402
from . import SWE_agent      # noqa: E402

__all__ = ['monologue_agent', 'codeact_agent',
           'planner_agent', 'SWE_agent']

# all_agents is a dict of name: agent_class
for agent in all_agents.values():
    name = agent['name']
    prompt = agent['prompt']

    anon_class = type(name, (MicroAgent,), {
        'prompt': prompt,
        'agentDefinition': agent,
    })

    Agent.register(name, anon_class)
