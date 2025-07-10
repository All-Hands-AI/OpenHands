import warnings

from openhands.controller.agent import Agent

try:
    from openhands.agenthub.browsing_agent.browsing_agent import BrowsingAgent

    Agent.register('BrowsingAgent', BrowsingAgent)
except ImportError:
    warnings.warn(
        'BrowsingAgent could not be loaded due to missing dependencies. Install with \'pip install "openhands-ai[browser]"\' to use this feature.',
        stacklevel=2,
    )
