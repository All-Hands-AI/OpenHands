"""Constants for OpenHands CLI settings."""

# LLM Models
SUPPORTED_MODELS = [
    'gpt-4o-mini',
    'gpt-4o',
    'gpt-4-turbo',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-haiku-20241022'
]

# Agent Types
SUPPORTED_AGENTS = [
    'CodeActAgent',
    'PlannerAgent'
]

# Default Settings
DEFAULT_MODEL = 'gpt-4o'
DEFAULT_AGENT_TYPE = 'CodeActAgent'
DEFAULT_CONFIRMATION_MODE = True

# UI Constants
HIDDEN_VALUE_DISPLAY = '***'
NOT_SET_DISPLAY = 'Not set'