from types import ModuleType
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# Import agents with error handling for optional dependencies
from openhands.agenthub import (  # noqa: E402
    codeact_agent,
    dummy_agent,
    loc_agent,
    readonly_agent,
)

# Import agents with optional dependencies
browsing_agent: Optional[ModuleType]
try:
    from openhands.agenthub import browsing_agent
except ImportError as e:
    print(f'Warning: Could not import browsing_agent: {e}')
    browsing_agent = None

visualbrowsing_agent: Optional[ModuleType]
try:
    from openhands.agenthub import visualbrowsing_agent
except ImportError as e:
    print(f'Warning: Could not import visualbrowsing_agent: {e}')
    visualbrowsing_agent = None

# Import tom_codeact_agent separately to handle any import issues
tom_codeact_agent: Optional[ModuleType]
try:
    from openhands.agenthub import tom_codeact_agent
except ImportError as e:
    print(f'Warning: Could not import tom_codeact_agent: {e}')
    tom_codeact_agent = None

from openhands.controller.agent import Agent  # noqa: E402

__all__ = [
    'Agent',
    'codeact_agent',
    'dummy_agent',
    'readonly_agent',
    'loc_agent',
]

# Add optional agents to __all__ if they were imported successfully
if browsing_agent is not None:
    __all__.append('browsing_agent')

if visualbrowsing_agent is not None:
    __all__.append('visualbrowsing_agent')

if tom_codeact_agent is not None:
    __all__.append('tom_codeact_agent')
