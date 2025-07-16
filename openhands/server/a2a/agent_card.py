import os

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

skill = AgentSkill(
    id='openhands_codeact_skill',
    name='OpenHands SWE Skill',
    description="A comprehensive skill that supports software development tasks.",
    tags=['code', 'execution', 'python', 'browsing', 'SWE'],
    examples=[
        # Users can specify which agent to invoke by adding the following metadata to their request:
        # "metadata": {"agent": "CodeActAgent"}
        # If this parameter is not specified, OpenHands' default agent will be invoked.
        # The following examples are for CodeActAgent:
        'Calculate the factorial of 10 in Python.',
        'Sort a list of numbers in descending order using Python.',
        'Get the current date and time in Python.',
    ],
)

BACKEND_HOST = os.environ.get('BACKEND_HOST', '127.0.0.1')
BACKEND_PORT = os.environ.get('BACKEND_PORT', '3000')

agent_card = AgentCard(
    name='OpenHands CodeAct Agent',
    description="A powerful agent for software development tasks.",
    url=f'http://{BACKEND_HOST}:{BACKEND_PORT}/a2a',
    version='1.0.0',
    defaultInputModes=['text/plain'],
    defaultOutputModes=['text/plain'],
    capabilities=AgentCapabilities(streaming=False),
    skills=[skill],
    supportsAuthenticatedExtendedCard=False,
)
