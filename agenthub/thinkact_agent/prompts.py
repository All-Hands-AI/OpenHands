
# '': '',

commands = {
    'search_for': {
        'params': '<keywords>',
        'description': 'Will allow you to search your working directory for files and folders that match your <keyword>.',
        'example': '''
    Thoughts:
    I need to search for "tree" so that I can find the decision tree classifier.

    Action:
    ```
    search_for tree
    ```'''
    },
    'edit ': {
        'params': '<filename>',
        'description': 'This will allow you to modify files within your working directory. Usage: "edit example.txt" -> opens the example.txt file and shows the first 100 lines',
        'example': '''
    Thoughts:
    I need to edit 'config.yaml' so that I can reproduce this bug.
    Action:
    ```
    edit config.yaml
    ```'''
    },
    'goto': {
        'params': '<line_num>',
        'description': 'This will allow you to go through a file to any line. Usage: "Goto 124" -> returns lines 124-224 within current file',
        'example': '''
    Thoughts:
    I need to modify the model so that it will perform better, lets find the code for the model.
    Action:
    ```
    goto 150
    ```'''
    },
    'scroll_up': {
        'params': '',
        'description': 'When you are in a file you can see the 100 lines above your current view. Usage: "scroll_up" -> returns the 100 lines above what you were reading',
        'example': '''
    Thoughts:
    I can't seem to find __init__ in the current window, we should scroll up to try and find it.
    Action:
    ```
    scroll_up
    ```'''
    },
    'scroll_down': {
        'params': '',
        'description': 'When you are in a file you can see the 100 lines below your current view. Usage: "scroll_down" -> returns the 100 lines below what you were reading',
        'example': '''
    Thoughts:
    I do not see the method that I need to modify `read_csv`, let's keep looking through the file.
    Action:
    ```
    scroll_down
    ```'''
    },
    'modify': {
        'params': '<start_line>:<end_line> "<replacement>"',
        'description': 'This will make changes to a file by deleting all lines from <start_line> to <end_line> and replacing them with <replacement>',
        'example': '''
    Thoughts:
    I have found the error, we need to change lines 223:225 so that it will print out the correctly formatted string.
    Action:
    ```
    modify 223:225 "\t\toutput = state.get_cur_state(n=1)\n\t\tprint(output)"
    ```'''
    },
}


def get_all_commands(cmds=commands):
    """Compiles all of the ACI commands into a documentation format"""
    docs = ''
    for k, v in cmds.items():
        docs += f'{k}:\n'
        docs += f'Usage: {k} {v["params"]}\n'
        docs += f'Description: {v["description"]}\n'
        docs += f'Example Usage:\n{v["example"]}\n\n'
    return docs


COMMANDS_LIST = f'''
Command documentation:
{get_all_commands()}

These commands will allow you to easily navigate the file system and make changes quickly.
'''

START_MESSAGE = f'''
You are an autonomous coding agent, here to provide solutions for coding issues. You have been given a custom interface, including some commands you can run.
{COMMANDS_LIST}
'''.strip()


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
