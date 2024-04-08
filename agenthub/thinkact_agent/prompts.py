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

RESPONSE_FORMAT = '''
Format:
    "Thoughts:
    <Some thoughts that you have on what to do next>
    Action to execute:
    ```
    <command> <params>
    ```"
'''

SYSTEM_MESSAGE = f'''
You are an autonomous coding agent, here to provide solutions for coding issues.
You have been given a custom interface, including some commands you can run.
{COMMAND_SEGMENT}
'''.strip()


def NO_ACTION(latest): return f'''
You did not include any action to take in your most recent output:

===== Output ======
{latest}
==== End Output ===

Remember these are the custom commands you can use:
{COMMAND_SEGMENT}

Lets try that again, it is very important that you adhere to the output format
This time, be sure to use the exact format below, replacing anything in <> with the appropriate value(s):
{RESPONSE_FORMAT}

It is crucial you use the format provided as the output will be parsed automatically.
'''


def STEP_PROMPT(step, task, dir, file): return f'''
You are currently on step {step} of your task:
{task}

Current working directory and file:
- Directory: {dir}
- File: {file}

Based on what you have done and the task that you are trying to complete output two things.
- First, think about what your next action should be and plan it out.
- Second, create a piece of code that will execute your next action.
    - The code MUST be surrounded in triple back ticks EXACTLY like this: ```\n<code>\n```
{RESPONSE_FORMAT}

Keep all of the guidelines above in mind when you are thinking and making code.
Please come up with a thought and action based on your current task and latest steps.
'''.strip()


def MEMORY_FORMAT(act, obs): return f'''
You performed this action:
'{act}'

The following happened as a result:
{obs}
'''.strip()


def CONTEXT_PROMPT(memory, window):
    res = f'These are your past {window} memories:\n'
    window_size = window if len(memory) > window else len(memory)
    cur_mems = memory[-window_size:]
    res += '===== Memories =====\n'
    for idx, mem in enumerate(cur_mems):
        res += f'\nMemory {idx}:\n{mem}\n'
    res += '======= End =======\n'
    res += 'Use these memories to provide additional context to the problem you are solving.\n'
    return res
