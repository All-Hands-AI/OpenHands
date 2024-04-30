---
sidebar_label: parser
title: agenthub.SWE_agent.parser
---

#### get\_action\_from\_string

```python
def get_action_from_string(command_string: str,
                           path: str,
                           line: int,
                           thoughts: str = '') -> Action | None
```

Parses the command string to find which command the agent wants to run
Converts the command into a proper Action and returns

#### parse\_command

```python
def parse_command(input_str: str, path: str, line: int)
```

Parses a given string and separates the command (enclosed in triple backticks) from any accompanying text.

**Arguments**:

- `input_str` _str_ - The input string to be parsed.
  

**Returns**:

- `tuple` - A tuple containing the command and the accompanying text (if any).

