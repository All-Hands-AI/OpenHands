import re


def split_bash_commands(command_string):
    def handle_heredoc(cmd_string):
        lines = cmd_string.split('\n')
        result = []
        i = 0
        in_heredoc = False
        heredoc_delimiter = None
        current_command = []

        while i < len(lines):
            line = lines[i].strip()
            if not in_heredoc and '<<' in line:
                heredoc_match = re.search(r'<<-?\s*(\w+)', line)
                if heredoc_match:
                    heredoc_delimiter = heredoc_match.group(1)
                    in_heredoc = True
                current_command.append(lines[i])
            elif in_heredoc:
                current_command.append(lines[i])
                if line == heredoc_delimiter:
                    in_heredoc = False
                    result.append('\n'.join(current_command))
                    current_command = []
            else:
                if current_command:
                    current_command.append(lines[i])
                else:
                    result.append(lines[i])
            i += 1

        if current_command:
            if in_heredoc:
                raise ValueError('Unclosed heredoc')
            result.append('\n'.join(current_command))

        return result

    def clean_command(cmd):
        in_quotes = False
        quote_char = None
        cleaned = []
        i = 0
        while i < len(cmd):
            char = cmd[i]
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif quote_char == char:
                    in_quotes = False
                    quote_char = None
                cleaned.append(char)
            elif (
                char == '\\'
                and i + 1 < len(cmd)
                and cmd[i + 1] == quote_char
                and cmd[i - 1] != '\\'
            ):
                # Handle escaped quote character ONLY if not preceded by a backslash
                cleaned.append(char)  # Append the backslash
                cleaned.append(cmd[i + 1])  # Append the quote character
                i += 1  # Skip the next character (quote)
            elif char == '#' and not in_quotes:
                break  # Ignore comments outside of quotes
            else:
                cleaned.append(char)
            i += 1
        # print(cleaned)
        return ''.join(cleaned).strip()

    def parse_commands(cmds):
        parsed_commands = []
        current_command = []
        in_quotes = False
        quote_char = None
        brace_level = 0
        for_level = 0
        escaped = False
        in_heredoc = False
        heredoc_delimiter = None

        for cmd in cmds:
            cmd_chars = list(cmd)
            i = 0
            while i < len(cmd_chars):
                char = cmd_chars[i]

                if escaped:
                    current_command.append(char)
                    escaped = False
                elif char == '\\':
                    escaped = True
                    current_command.append(char)
                elif in_heredoc:
                    current_command.append(char)
                    if cmd[i:].startswith(heredoc_delimiter):
                        in_heredoc = False
                        heredoc_delimiter = None
                elif char in ('"', "'"):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif quote_char == char:
                        in_quotes = False
                        quote_char = None
                    current_command.append(char)
                elif char == '{':
                    brace_level += 1
                    current_command.append(char)
                elif char == '}':
                    brace_level -= 1
                    current_command.append(char)
                elif (
                    char == ';'
                    and not in_quotes
                    and brace_level == 0
                    and for_level == 0
                ):
                    if current_command:
                        parsed_commands.append(''.join(current_command).strip())
                        current_command = []
                elif char == '#' and not in_quotes:
                    break  # Ignore comments outside of quotes
                else:
                    current_command.append(char)

                if not in_heredoc and '<<' in ''.join(current_command[-2:]):
                    heredoc_match = re.search(r'<<-?\s*(\w+)', ''.join(current_command))
                    if heredoc_match:
                        in_heredoc = True
                        heredoc_delimiter = heredoc_match.group(1)

                if ''.join(current_command).strip().startswith('for '):
                    for_level += 1
                elif ''.join(current_command).strip() == 'done' and for_level > 0:
                    for_level -= 1

                i += 1

            if current_command:
                parsed_commands.append(''.join(current_command).strip())
                current_command = []

        if in_quotes:
            raise ValueError('Unclosed quote')
        if in_heredoc:
            raise ValueError('Unclosed heredoc')

        return parsed_commands

    # Handle heredocs first
    try:
        preprocessed_commands = handle_heredoc(command_string)
    except ValueError as e:
        raise ValueError(str(e))

    # Clean and parse commands
    cleaned_commands = [clean_command(cmd) for cmd in preprocessed_commands]
    parsed_commands = parse_commands(cleaned_commands)

    # Filter out empty commands and join multi-line commands
    result = []
    current_command = []
    for cmd in parsed_commands:
        if cmd.endswith('\\') and not cmd.endswith('\\\\'):
            current_command.append(cmd[:-1])  # Remove the trailing backslash
        else:
            if current_command:
                current_command.append(cmd)
                result.append(clean_command(' '.join(current_command)))
                current_command = []
            else:
                result.append(clean_command(cmd))

    if current_command:
        result.append(clean_command(' '.join(current_command)))

    return [cmd.strip() for cmd in result if cmd.strip()]
