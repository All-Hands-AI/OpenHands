import tomllib

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

def get_or_error(key: str):
    """
    Get a key from the config, or raise an error if it doesn't exist.
    """
    if key not in config:
        raise KeyError(f"Please set '{key}' in `config.toml`.")
    return config[key]

def get_or_default(key: str, default):
    """
    Get a key from the config, or return a default value if it doesn't exist.
    """
    return config.get(key, default)

def get_or_none(key: str):
    """
    Get a key from the config, or return None if it doesn't exist.
    """
    return config.get(key, None)
