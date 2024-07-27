import bashlex


def split_bash_commands(commands):
    try:
        parsed = bashlex.parse(commands)
    except bashlex.errors.ParsingError:
        # If parsing fails, return the original commands
        return commands

    result: list[str] = []
    last_end = 0

    for node in parsed:
        start, end = node.pos

        # Include any text between the last command and this one
        if start > last_end:
            between = commands[last_end:start]
            if result:
                result[-1] += between
            elif between.strip():
                # THIS SHOULD NOT HAPPEN
                result.append(between.strip())

        # Extract the command, preserving original formatting
        command = commands[start:end]
        if command.strip():
            result.append(command)

        last_end = end

    # Add any remaining text after the last command to the last command
    if last_end < len(commands) and result:
        result[-1] += commands[last_end:]
    elif last_end < len(commands):
        remaining = commands[last_end:].strip()
        if remaining:
            result.append(remaining)

    return result
