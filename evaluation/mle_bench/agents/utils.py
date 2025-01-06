import os
import re
from typing import Optional


def get_env_var(value: str) -> Optional[str]:
    """Returns the name of the environment variable in the format `${secrets.<name>}`."""

    if not isinstance(value, str):
        return None

    env_var_pattern = r'\$\{\{\s*secrets\.(\w+)\s*\}\}'
    match = re.match(env_var_pattern, value)

    if not match:
        return None

    return match.group(1)


def is_env_var(value: str) -> bool:
    """Checks if the value is an environment variable."""

    return get_env_var(value) is not None


def parse_env_var_values(dictionary: dict) -> dict:
    """
    Parses any values in the dictionary that match the ${{ secrets.ENV_VAR }} pattern and replaces
    them with the value of the ENV_VAR environment variable.
    """
    for key, value in dictionary.items():
        if not is_env_var(value):
            continue

        env_var = get_env_var(value)

        if os.getenv(env_var) is None:
            raise ValueError(f'Environment variable `{env_var}` is not set!')

        dictionary[key] = os.getenv(env_var)

    return dictionary
