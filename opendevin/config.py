import os
import tomllib

from dotenv import load_dotenv

load_dotenv()

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

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
