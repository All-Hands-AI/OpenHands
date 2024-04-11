from opendevin.action import (
    Action,
    AgentFinishAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    BrowseURLAction,
    AgentEchoAction,
)

import re

from .prompts import DEFAULT_COMMAND_STR, COMMAND_SEGMENT

# commands: exit, read, write, browse, kill, search_file, search_dir


def get_action_from_string(command_string: str) -> Action | None:
    """
    Parses the command string to find which command the agent wants to run
    Converts the command into a proper Action and returns
    """
    vars = command_string.split(' ')
    cmd = vars[0]
    args = [] if len(vars) == 1 else ' '.join(vars[1:])

    # TODO: add exception handling for improper commands
    if 'exit' == cmd:
        return AgentFinishAction()

    elif 'read' == cmd:
        rex = r'^read\s+(\S+)(?:\s+(\d+))?$'
        valid = re.match(rex, command_string, re.DOTALL)
        if valid:
            file, start = valid.groups()

            start = 0 if not start else int(start)

            return FileReadAction(file, start)
        else:
            return AgentEchoAction(f'Invalid command structure for\n ```\n{command_string}\n```.\nTry again using this format:\n{DEFAULT_COMMAND_STR}')

    elif 'write' == cmd:
        rex = r'^write\s+(\S+)\s+(\S.*)\s*(?:(\d+)s*(\d+))?$'
        valid = re.match(rex, command_string, re.DOTALL)

        if valid:
            file, content, start, end = valid.groups()

            start = 0 if not start else int(start)
            end = -1 if not end else int(end)

            return FileWriteAction(file, content, start, end)
        else:
            return AgentEchoAction(f'Invalid command structure for\n ```\n{command_string}\n```.\nTry again using this format:\n{DEFAULT_COMMAND_STR}')

    elif 'browse' == cmd:
        return BrowseURLAction(args[0].strip())

    elif cmd in ['search_file', 'search_dir', 'find_file']:
        rex = r'^(search_file|search_dir|find_file)\s+(\S+)(?:\s+(\S+))?$'
        valid = re.match(rex, command_string, re.DOTALL)
        if valid:
            return CmdRunAction(command_string)
        else:
            return AgentEchoAction(f'Invalid command structure for\n ```\n{command_string}\n```.\nTry again using this format:\n{COMMAND_SEGMENT}')
    else:
        # check bash command
        obs = str(CmdRunAction(f'type {cmd}'))
        if obs.split(':')[-1].strip() == 'not found':
            # echo not found error for llm
            return AgentEchoAction(content=obs)
        else:
            # run valid command
            return CmdRunAction(command_string)


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
        if action:
            ind = 2 if len(parts) > 2 else 1
            accompanying_text = ''.join(parts[:-ind]).strip()
            return action, accompanying_text

    return None, input_str  # used for retry
