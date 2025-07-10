# Run this file to trigger a model download
import warnings

try:
    import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
except ImportError as e:
    warnings.warn(
        f'Could not import openhands.agenthub: {e}. Some features may not be available.',
        stacklevel=2,
    )

print('OpenHands download check completed.')
