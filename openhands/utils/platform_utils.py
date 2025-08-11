import re
import sys


def refine_prompt(prompt: str) -> str:
    """Refine prompt for platform-specific commands.

    On Windows, replaces 'bash' with 'powershell' in prompts.

    Args:
        prompt: The prompt text to refine

    Returns:
        The refined prompt text
    """
    if sys.platform == 'win32':
        # Replace 'bash' with 'powershell' including tool names like 'execute_bash'
        # First replace 'execute_bash' with 'execute_powershell' to handle tool names
        result = re.sub(
            r'\bexecute_bash\b', 'execute_powershell', prompt, flags=re.IGNORECASE
        )
        # Then replace standalone 'bash' with 'powershell'
        result = re.sub(
            r'(?<!execute_)(?<!_)\bbash\b', 'powershell', result, flags=re.IGNORECASE
        )
        return result
    return prompt
