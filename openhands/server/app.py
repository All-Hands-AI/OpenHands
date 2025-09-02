"""OpenHands FastAPI application.

This module provides the main FastAPI application for OpenHands.
For extensibility and custom configurations, use the factory pattern
from openhands.server.factory instead of importing this app directly.
"""

from openhands.server.factory import create_default_app

# Create the default OpenHands app using the factory
app = create_default_app()
