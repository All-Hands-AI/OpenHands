from opendevin.parse_commands import parse_command_file

COMMAND_DOCS = parse_command_file()

COMMAND_SEGMENT = (
    f"""

Apart from the standard bash commands, you can also use the following special commands:
{COMMAND_DOCS}
"""
    if COMMAND_DOCS is not None
    else ''
)

START_MESSAGE = f'''
You are an autonomous coding agent, here to provide solutions for coding issues. You have been given a custom interface, including some commands you can run.
{COMMAND_SEGMENT}
'''.strip()


def NO_ACTION(latest): return f'''
You did not include any action to take in your most rescent output:

===== Output ======
{latest}
==== End Output ===

Lets try that again, it is very important that you adhere to the output format
This time, be sure to use the exact format below, replacing anything in <> with the appropriate value(s):
Thoughts:
Some thoughts that you have on what to do next
Action:
```
<command> <params>
```

'''


def STEP_PROMPT(step, task, dir, file, context): return f'''
You are currently on step {step} of your task:
{task}

Current working directory and file:
- Directory: {dir}
- File: {file}

These are the last few steps that you have performed for context:
{context}

Based on what you have just done and the task that you are trying to complete output two things.
First, think about what your next action should be and plan it out.
Second, create a piece of code that will execute your next action.

Example:
Thought:
I need to search for "tree" so I can find the file where the DecisionTreeClassifier is located.

Action:
```
search_for tree
```

'''.strip()


def MEMORY_FORMAT(act, obs): return f'''
You performed this action:
'{act}'

The following happened as a result:
{obs}
'''.strip()
