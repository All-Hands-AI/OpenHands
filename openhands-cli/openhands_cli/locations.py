import os

# Configuration directory for storing agent settings and CLI configuration
PERSISTENCE_DIR = os.path.expanduser('~/.openhands')
CONVERSATIONS_DIR = os.path.join(PERSISTENCE_DIR, 'conversations')

# Working directory for agent operations (current directory where CLI is run)
WORK_DIR = os.getcwd()

AGENT_SETTINGS_PATH = 'agent_settings.json'

# MCP configuration file (relative to PERSISTENCE_DIR)
MCP_CONFIG_FILE = 'mcp.json'
