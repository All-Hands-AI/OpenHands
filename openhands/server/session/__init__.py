# Backward-compatible import for the web server-bound session wrapper.
# The canonical name is WebSession; Session remains as an alias for BC.
from openhands.server.session.session import WebSession
from openhands.server.session.session import WebSession as Session

__all__ = ['WebSession', 'Session']
