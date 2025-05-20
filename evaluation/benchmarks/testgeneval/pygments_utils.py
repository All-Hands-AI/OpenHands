import re

from pygments.lexers.python import PythonLexer


def tokenize_code(code):
    lexer = PythonLexer()
    tokens = process_pygments_tokens(lexer.get_tokens(code))
    return tokens


def process_pygments_tokens(tokens):
    new_tokens = []

    for token in tokens:
        if (
            str(token[0]) == 'Token.Text'
            and re.match(r'\s+', token[1])
            or str(token[0]) == 'Token.Text.Whitespace'
        ):
            continue
        new_tokens.append(token[1])

    new_tokens_final = []
    i = 0
    while i < len(new_tokens) - 2:
        if (
            new_tokens[i] == '"'
            and new_tokens[i + 1] == 'STR'
            and new_tokens[i + 2] == '"'
        ):
            new_tokens_final.append('"STR"')
            i = i + 3
        else:
            new_tokens_final.append(new_tokens[i])
            i = i + 1

    for i in range(len(new_tokens) - 2, len(new_tokens)):
        if i >= 0:
            new_tokens_final.append(new_tokens[i])

    return new_tokens_final
