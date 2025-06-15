import os

from openhands.core.logger import openhands_logger as logger

DEFAULT_PROMPT_DIR = '.openhands-user/prompts'
CUSTOM_SYSTEM_APPEND_FILENAME = 'custom_system_append.txt'
CUSTOM_TOOL_APPEND_FILENAME = 'custom_tool_append.txt'


def get_custom_prompt_addition(filename: str, workspace_root: str | None) -> str:
    """
    Reads a custom prompt file from the .openhands-user/prompts directory.

    Args:
        filename: The name of the file in .openhands-user/prompts/
                  (e.g., "custom_system_append.txt").
        workspace_root: The absolute path to the OpenHands workspace root.
                        If None, custom prompts will not be loaded.

    Returns:
        The content of the file as a string, or an empty string if not found or on error.
    """
    if not workspace_root:
        return ''

    custom_prompt_path = os.path.join(workspace_root, DEFAULT_PROMPT_DIR, filename)
    if os.path.exists(custom_prompt_path):
        try:
            with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(
                f'Could not read custom prompt file {custom_prompt_path}: {e}'
            )
            return ''
    return ''
