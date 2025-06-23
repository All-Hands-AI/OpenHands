import os

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

skill = AgentSkill(
    id='openhands_agents',
    name='openhands_agents',
    description="An integration layer that allows agents defined in OpenHands' agenthub to be accessible and operable via the A2A protocol.",
    tags=['code', 'execution', 'python', 'llm', 'browsing', 'contains'],
    examples=[
        'When sending a request using A2A,',
        'include the following metadata in the "message" parameter:',
        '"metadata": { "agent": "CodeActAgent" },',
        'This allows the request to be routed to the desired agent.',
        'The target agents are,[BrowsingAgent, CodeActAgent, DummyAgent, ReadOnlyAgent, VisualBrowsingAgent].etc..',
        'If we extract from CodeActAgent,',
        'Calculate the factorial of 10 in Python.',
        'Sort a list of numbers in descending order using Python.',
        'Get the current date and time in Python.',
    ],
)

BACKEND_HOST = os.environ.get('BACKEND_HOST', '127.0.0.1')
BACKEND_PORT = os.environ.get('BACKEND_PORT', '3000')

agent_card = AgentCard(
    name='Hello openhands_agents Agent',
    description="An integration layer that allows agents defined in OpenHands' agenthub to be accessible and operable via the A2A protocol.",
    url=f'http://{BACKEND_HOST}:{BACKEND_PORT}/a2a',
    version='1.0.0',
    defaultInputModes=['text/plain'],
    defaultOutputModes=['text/plain'],
    capabilities=AgentCapabilities(streaming=False),
    skills=[skill],
    supportsAuthenticatedExtendedCard=False,
)
