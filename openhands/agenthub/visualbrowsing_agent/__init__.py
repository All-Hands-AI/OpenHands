try:
    from openhands.agenthub.visualbrowsing_agent.visualbrowsing_agent import (
        VisualBrowsingAgent,
    )
    from openhands.controller.agent import Agent

    Agent.register('VisualBrowsingAgent', VisualBrowsingAgent)
except ImportError:
    # VisualBrowsingAgent requires browsergym which may not be available
    pass
