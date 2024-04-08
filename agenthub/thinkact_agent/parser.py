from opendevin.action import (
    Action,
    AgentFinishAction,
    CmdRunAction,
)


def get_action_from_string(command_string: str) -> Action:
    """
    Parses the command string to find which command the agent wants to run
    Converts the command into a proper Action and returns
    """
    vars = command_string.split(' ')
    cmd = vars[0]
    args = [] if len(vars) == 1 else vars[0:]
    bg = True if '--background' in args else False

    if 'exit' == cmd:
        return AgentFinishAction()

    # TODO: need to integrate all of the custom commands

    else:
        return CmdRunAction(command_string, background=bg)


def parse_command(input_str: str):
    """
    Parses a given string and separates the command (enclosed in triple backticks) from any accompanying text.

    Args:
        input_str (str): The input string to be parsed.

    Returns:
        tuple: A tuple containing the command and the accompanying text (if any).
    """
    input_str = input_str.strip()
    if '```' in input_str:
        parts = input_str.split('```')
        command_str = parts[1].strip()
        action = get_action_from_string(command_str)
        ind = 2 if len(parts) > 2 else 1
        accompanying_text = ''.join(parts[:-ind]).strip()
        return action, accompanying_text
    else:
        return None, input_str
