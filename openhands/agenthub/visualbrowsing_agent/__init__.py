import warnings

from openhands.controller.agent import Agent

try:
    from openhands.agenthub.visualbrowsing_agent.visualbrowsing_agent import (
        VisualBrowsingAgent,
    )

    Agent.register('VisualBrowsingAgent', VisualBrowsingAgent)
except ImportError:
    warnings.warn(
        'VisualBrowsingAgent could not be loaded due to missing dependencies. Install with \'pip install "openhands-ai[browser]"\' to use this feature.',
        stacklevel=2,
    )
