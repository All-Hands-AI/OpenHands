from opendevin.action import (
    Action,
    AgentFinishAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    BrowseURLAction,
)

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
        if len(args) == 1:
            file = args[0]
            start = 0
        elif len(args) == 2:
            file, start = args[0], int(args[1])
        elif len(args) > 2:
            file, start = args[0], int(args[1])
        else:
            return None

        return FileReadAction(file, start)

    elif 'write' == cmd:
        assert len(args) >= 4, 'Not enough arguments for this command'
        file = args[0]
        start, end = [int(arg) for arg in args[1:3]]
        content = ' '.join(args[3:])
        return FileWriteAction(file, content, start, end)

    elif 'browse' == cmd:
        return BrowseURLAction(args[0].strip())

    # TODO: need to integrate all of the custom commands

    else:
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
