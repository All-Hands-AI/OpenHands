# Backward-compatible import for the web server-bound session wrapper.
# The canonical name is WebSession; Session is an alias to be removed later.
from openhands.server.session.session import WebSession
from openhands.server.session.session import WebSession as Session

__all__ = ['WebSession', 'Session']
