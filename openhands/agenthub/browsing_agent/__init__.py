try:
    from openhands.agenthub.browsing_agent.browsing_agent import BrowsingAgent
    from openhands.controller.agent import Agent

    Agent.register('BrowsingAgent', BrowsingAgent)
except ImportError:
    # BrowsingAgent requires browsergym which may not be available
    pass
