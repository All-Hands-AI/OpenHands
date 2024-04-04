import os
import toml

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG = {
    "LLM_API_KEY": None,
    "LLM_BASE_URL": None,
    "WORKSPACE_DIR": os.path.join(os.getcwd(), "workspace"),
    "LLM_MODEL": "gpt-4-0125-preview",
    "SANDBOX_CONTAINER_IMAGE": "ghcr.io/opendevin/sandbox",
    "RUN_AS_DEVIN": "false",
    "LLM_EMBEDDING_MODEL": "local",
    "LLM_NUM_RETRIES": 6,
    "LLM_COOLDOWN_TIME" : 1,
    "DIRECTORY_REWRITE" : "",
    "PROMPT_DEBUG_DIR": "",
    "MAX_ITERATIONS": 100,
}

config_str = ""
if os.path.exists("config.toml"):
    with open("config.toml", "rb") as f:
        config_str = f.read().decode("utf-8")

tomlConfig = toml.loads(config_str)
config = DEFAULT_CONFIG.copy()
for key, value in config.items():
  if key in os.environ:
    config[key] = os.environ[key]
  elif key in tomlConfig:
    config[key] = tomlConfig[key]


def _get(key: str, default):
    value = config.get(key, default)
    if not value:
        value = os.environ.get(key, default)
    return value

def get_or_error(key: str):
    """
    Get a key from the config, or raise an error if it doesn't exist.
    """
    value = get_or_none(key)
    if not value:
        raise KeyError(f"Please set '{key}' in `config.toml` or `.env`.")
    return value

def get_or_default(key: str, default):
    """
    Get a key from the config, or return a default value if it doesn't exist.
    """
    return _get(key, default)

def get_or_none(key: str):
    """
    Get a key from the config, or return None if it doesn't exist.
    """
    return _get(key, None)

def get(key: str):
    """
    Get a key from the config, please make sure it exists.
    """
    return config.get(key)
