import json
import os
from pathlib import Path
from typing import Optional

# Configuration directory for storing agent settings and CLI configuration
PERSISTENCE_DIR = os.path.expanduser('~/.openhands')
CONVERSATIONS_DIR = os.path.join(PERSISTENCE_DIR, 'conversations')

AGENT_SETTINGS_PATH = 'agent_settings.json'

# MCP configuration file (relative to PERSISTENCE_DIR)
MCP_CONFIG_FILE = 'mcp.json'

# CLI settings file (relative to PERSISTENCE_DIR)
CLI_SETTINGS_FILE = 'oh_cli_settings.json'


def get_configured_working_directory() -> Optional[str]:
    """Get the configured working directory from CLI settings.
    
    Returns:
        The configured working directory path if set, None otherwise.
    """
    try:
        cli_settings_path = Path(PERSISTENCE_DIR) / CLI_SETTINGS_FILE
        if cli_settings_path.exists():
            with open(cli_settings_path, 'r') as f:
                settings = json.load(f)
                working_dir = settings.get('working_directory')
                if working_dir and os.path.exists(working_dir):
                    return working_dir
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_working_directory(working_dir: str) -> None:
    """Save the working directory to CLI settings.
    
    Args:
        working_dir: The working directory path to save.
    """
    # Ensure persistence directory exists
    os.makedirs(PERSISTENCE_DIR, exist_ok=True)
    
    cli_settings_path = Path(PERSISTENCE_DIR) / CLI_SETTINGS_FILE
    
    # Load existing settings or create new ones
    settings = {}
    if cli_settings_path.exists():
        try:
            with open(cli_settings_path, 'r') as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            settings = {}
    
    # Update working directory
    settings['working_directory'] = working_dir
    
    # Save settings
    with open(cli_settings_path, 'w') as f:
        json.dump(settings, f, indent=2)


# Working directory for agent operations
# First try to get configured directory, fallback to current directory
WORK_DIR = get_configured_working_directory() or os.getcwd()
