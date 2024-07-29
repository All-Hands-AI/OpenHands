def split_bash_commands(commands):
    # States
    NORMAL = 0
    IN_SINGLE_QUOTE = 1
    IN_DOUBLE_QUOTE = 2
    IN_HEREDOC = 3

    state = NORMAL
    heredoc_trigger = None
    result = []
    current_command: list[str] = []

    i = 0
    while i < len(commands):
        char = commands[i]

        if state == NORMAL:
            if char == "'":
                state = IN_SINGLE_QUOTE
            elif char == '"':
                state = IN_DOUBLE_QUOTE
            elif char == '\\':
                # Check if this is escaping a newline
                if i + 1 < len(commands) and commands[i + 1] == '\n':
                    current_command.append(char)  # Append the backslash
                    current_command.append(commands[i + 1])  # Append the newline
                    i += 1  # Skip the newline
                    # Preserve indentation after backslash-newline
                    j = i + 1
                    num_spaces = 0
                    while (
                        j < len(commands)
                        and commands[j].isspace()
                        and commands[j] != '\n'
                    ):
                        num_spaces += 1
                        j += 1
                    # Append the exact whitespace
                    current_command.append(commands[j - 1 - num_spaces : j])
                    current_command.append(commands[j:].split('\n', 1)[0].lstrip())
                    i = j + len(commands[j:].split('\n', 1)[0])
                elif i + 1 < len(commands) and commands[i + 1] == '-':
                    # If backslash is escaping a '-', skip the backslash
                    i += 1  # Skip the backslash and append the '-'
                    current_command.append(commands[i])
                else:
                    # If backslash is escaping another character, append the backslash and the escaped character
                    current_command.append(commands[i : i + 2])
                    i += 1
            elif char == '\n':
                if not heredoc_trigger:
                    if current_command and current_command[-1] == '\\':
                        # Remove the backslash and continue the command
                        current_command.pop()
                        # Preserve indentation after backslash-newline
                        j = i + 1
                        while (
                            j < len(commands)
                            and commands[j].isspace()
                            and commands[j] != '\n'
                        ):
                            if commands[j] == '\\':
                                break
                            current_command.append(commands[j])
                            j += 1
                        i = j - 1  # Adjust i to the last space character

                    elif current_command and any(
                        c in current_command for c in ['&&', '||', '|', '&']
                    ):
                        # If the current command contains a control operator,
                        # continue to the next line
                        current_command.append(char)

                    elif current_command:
                        # Check if the next line is a comment
                        next_non_space = commands[i + 1 :].lstrip()
                        if next_non_space.startswith('#'):
                            current_command.append('\n')
                            current_command.append(next_non_space.split('\n', 1)[0])
                            i += len(next_non_space.split('\n', 1)[0])
                        else:
                            # Remove trailing whitespace
                            while current_command and current_command[-1].isspace():
                                current_command.pop()
                            result.append(''.join(current_command))
                            current_command = []
                    else:
                        # Handle empty lines between commands
                        j = i + 1
                        while (
                            j < len(commands)
                            and commands[j].isspace()
                            and commands[j] != '\n'
                        ):
                            j += 1
                        if j < len(commands) and commands[j] == '\n':
                            # Empty line, skip it
                            i = j
                        else:
                            result.append(''.join(current_command).strip())
                            current_command = []
            elif char == '<' and commands[i : i + 2] == '<<':
                # Detect heredoc
                state = IN_HEREDOC
                i += 2  # Skip '<<'
                while commands[i] == ' ':
                    i += 1
                start = i
                while commands[i] not in [' ', '\n']:
                    i += 1
                heredoc_trigger = commands[start:i]
                current_command.append(commands[start - 2 : i])  # Include '<<'
                continue  # Skip incrementing i at the end of the loop
            current_command.append(char)

        elif state == IN_SINGLE_QUOTE:
            current_command.append(char)
            if char == "'" and commands[i - 1] != '\\':
                state = NORMAL

        elif state == IN_DOUBLE_QUOTE:
            current_command.append(char)
            if char == '"' and commands[i - 1] != '\\':
                state = NORMAL

        elif state == IN_HEREDOC:
            current_command.append(char)
            if (
                char == '\n'
                and heredoc_trigger
                and commands[i + 1 : i + 1 + len(heredoc_trigger) + 1]
                == heredoc_trigger + '\n'
            ):
                # Check if the next line starts with the heredoc trigger followed by a newline
                i += (
                    len(heredoc_trigger) + 1
                )  # Move past the heredoc trigger and newline
                current_command.append(
                    heredoc_trigger + '\n'
                )  # Include the heredoc trigger and newline
                result.append(''.join(current_command).strip())
                current_command = []
                heredoc_trigger = None
                state = NORMAL
                continue

        i += 1

    # Add the last command if any
    if current_command:
        result.append(''.join(current_command))

    # Remove any empty strings and strip leading/trailing whitespace
    result = [cmd.strip() for cmd in result if cmd.strip()]

    return result
