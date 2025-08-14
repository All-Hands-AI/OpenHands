from dotenv import load_dotenv

load_dotenv()


from openhands.agenthub import (  # noqa: E402
    codeact_agent,
    dummy_agent,
    loc_agent,
    readonly_agent,
)

try:
    from openhands.agenthub import browsing_agent

    BROWSING_AGENT_AVAILABLE = True
except ImportError:
    BROWSING_AGENT_AVAILABLE = False

    # Create a mock module
    class MockBrowsingModule:
        pass

    browsing_agent = MockBrowsingModule()  # type: ignore

try:
    from openhands.agenthub import visualbrowsing_agent

    VISUALBROWSING_AGENT_AVAILABLE = True
except ImportError:
    VISUALBROWSING_AGENT_AVAILABLE = False

    # Create a mock module
    class MockVisualBrowsingModule:
        pass

    visualbrowsing_agent = MockVisualBrowsingModule()  # type: ignore
from openhands.controller.agent import Agent  # noqa: E402

__all__ = [
    'Agent',
    'codeact_agent',
    'dummy_agent',
    'readonly_agent',
    'loc_agent',
]

if BROWSING_AGENT_AVAILABLE:
    __all__.append('browsing_agent')

if VISUALBROWSING_AGENT_AVAILABLE:
    __all__.append('visualbrowsing_agent')
