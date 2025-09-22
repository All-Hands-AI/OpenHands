import os

# Configuration directory for storing agent settings and CLI configuration
PERSISTENCE_DIR = os.path.expanduser("~/.openhands")

# Working directory for agent operations (current directory where CLI is run)
WORK_DIR = os.getcwd()

AGENT_SETTINGS_PATH = "agent_settings.json"
