import re

from opendevin.events.action import (
    Action,
    AgentEchoAction,
    AgentFinishAction,
    AgentThinkAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
)

from .prompts import COMMAND_USAGE, CUSTOM_DOCS

# commands: exit, read, write, browse, kill, search_file, search_dir

no_open_file_error = AgentEchoAction(
    'You are not currently in a file. You can use the read command to open a file and then use goto to navigate through it.'
)


def invalid_error(cmd, docs):
    return f"""ERROR:
Invalid command structure for
```
{cmd}
```
You may have caused this error by having multiple commands within your command block.
If so, try again by running only one of the commands:

Try again using this format:
{COMMAND_USAGE[docs]}
"""


def get_action_from_string(
    command_string: str, path: str, line: int, thoughts: str = ''
) -> Action | None:
    """
    Parses the command string to find which command the agent wants to run
    Converts the command into a proper Action and returns
    """
    vars = command_string.split(' ')
    cmd = vars[0]
    args = [] if len(vars) == 1 else vars[1:]

    if 'exit' == cmd:
        return AgentFinishAction()

    elif 'think' == cmd:
        return AgentThinkAction(' '.join(args))

    elif 'scroll_up' == cmd:
        if not path:
            return no_open_file_error
        return FileReadAction(path, line + 100, line + 200, thoughts)

    elif 'scroll_down' == cmd:
        if not path:
            return no_open_file_error
        return FileReadAction(path, line - 100, line, thoughts)

    elif 'goto' == cmd:
        if not path:
            return no_open_file_error
        rex = r'^goto\s+(\d+)$'
        valid = re.match(rex, command_string)
        if valid:
            start = int(valid.group(1))
            end = start + 100
            return FileReadAction(path, start, end, thoughts)
        else:
            return AgentEchoAction(invalid_error(command_string, 'goto'))

    elif 'edit' == cmd:
        if not path:
            return no_open_file_error
        rex = r'^edit\s+(\d+)\s+(-?\d+)\s+(\S.*)$'
        valid = re.match(rex, command_string, re.DOTALL)
        if valid:
            start = int(valid.group(1))
            end = int(valid.group(2))
            change = valid.group(3)
            if '"' == change[-1] and '"' == change[0]:
                change = change[1:-1]
            return FileWriteAction(path, change, start, end, thoughts)
        else:
            return AgentEchoAction(invalid_error(command_string, 'edit'))

    elif 'read' == cmd:
        rex = r'^read\s+(\S+)(?:\s+(\d+))?(?:\s+(-?\d+))?$'
        valid = re.match(rex, command_string, re.DOTALL)
        if valid:
            file = valid.group(1)
            start_str = valid.group(2)
            end_str = valid.group(3)

            start = 0 if not start_str else int(start_str)
            end = -1 if not end_str else int(end_str)

            return FileReadAction(file, start, end, thoughts)
        else:
            return AgentEchoAction(invalid_error(command_string, 'read'))

    elif 'write' == cmd:
        rex = r'^write\s+(\S+)\s+(.*?)\s*(\d+)?\s*(-?\d+)?$'
        valid = re.match(rex, command_string, re.DOTALL)

        if valid:
            file = valid.group(1)
            content = valid.group(2)
            start_str = valid.group(3)
            end_str = valid.group(4)

            start = 0 if not start_str else int(start_str)
            end = -1 if not end_str else int(end_str)

            if '"' == content[-1] and '"' == content[0]:
                content = content[1:-1]

            return FileWriteAction(file, content, start, end, thoughts)
        else:
            return AgentEchoAction(invalid_error(command_string, 'write'))

    elif 'browse' == cmd:
        return BrowseURLAction(args[0].strip())

    elif cmd in ['search_file', 'search_dir', 'find_file']:
        rex = r'^(search_file|search_dir|find_file)\s+(\S+)(?:\s+(\S+))?$'
        valid = re.match(rex, command_string, re.DOTALL)
        if valid:
            return CmdRunAction(command_string)
        else:
            return AgentEchoAction(
                f'Invalid command structure for\n ```\n{command_string}\n```.\nTry again using this format:\n{CUSTOM_DOCS}'
            )
    else:
        # check bash command
        obs = str(CmdRunAction(f'type {cmd}'))
        if obs.split(':')[-1].strip() == 'not found':
            # echo not found error for llm
            return AgentEchoAction(content=obs)
        else:
            # run valid command
            return CmdRunAction(command_string)


def parse_command(input_str: str, path: str, line: int):
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
        ind = 2 if len(parts) > 2 else 1
        accompanying_text = ''.join(parts[:-ind]).strip()
        action = get_action_from_string(command_str, path, line, accompanying_text)
        if action:
            return action, accompanying_text
    return None, input_str  # used for retry
