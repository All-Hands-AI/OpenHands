import os
import shutil

import pytest

from opendevin.utils.prompt import PromptManager


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "agenthub/codeact_agent" to the temp directory
    shutil.copytree('agenthub/codeact_agent', tmp_path, dirs_exist_ok=True)

    # Return the temporary directory path
    return tmp_path


SAMPLE_AGENT_SKILLS_DOCS = """Sample agent skills documentation"""


@pytest.fixture
def agent_skills_docs():
    return SAMPLE_AGENT_SKILLS_DOCS


CODEACT_SYSTEM_PROMPT = f"""A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.
The assistant can use an interactive Python (Jupyter Notebook) environment, executing code with <execute_ipython>.
<execute_ipython>
print("Hello World!")
</execute_ipython>
The assistant can execute bash commands on behalf of the user by wrapping them with <execute_bash> and </execute_bash>.

For example, you can list the files in the current directory by <execute_bash> ls </execute_bash>.
Important, however: do not run interactive commands. You do not have access to stdin.
Also, you need to handle commands that may run indefinitely and not return a result. For such cases, you should redirect the output to a file and run the command in the background to avoid blocking the execution.
For example, to run a Python script that might run indefinitely without returning immediately, you can use the following format: <execute_bash> python3 app.py > server.log 2>&1 & </execute_bash>
Also, if a command execution result saying like: Command: "npm start" timed out. Sending SIGINT to the process, you should also retry with running the command in the background.

The assistant can browse the Internet with <execute_browse> and </execute_browse>.
For example, <execute_browse> Tell me the usa's president using google search </execute_browse>.
Or <execute_browse> Tell me what is in http://example.com </execute_browse>.

The assistant can install Python packages using the %pip magic command in an IPython environment by using the following syntax: <execute_ipython> %pip install [package needed] </execute_ipython> and should always import packages and define variables before starting to use them.

Apart from the standard Python library, the assistant can also use the following functions (already imported) in <execute_ipython> environment:
{SAMPLE_AGENT_SKILLS_DOCS}
Please note that THE `edit_file_by_replace`, `append_file` and `insert_content_at_line` FUNCTIONS REQUIRE PROPER INDENTATION. If the assistant would like to add the line '        print(x)', it must fully write that out, with all those spaces before the code! Indentation is important and code that is not indented correctly will fail and require fixing before it can be run.

Responses should be concise.
The assistant should attempt fewer things at a time instead of putting too many commands OR too much code in one "execute" block.
Include ONLY ONE <execute_ipython>, <execute_bash>, or <execute_browse> per response, unless the assistant is finished with the task or needs more input or action from the user in order to proceed.
If the assistant is finished with the task you MUST include <finish></finish> in your response.
IMPORTANT: Execute code using <execute_ipython>, <execute_bash>, or <execute_browse> whenever possible.
When handling files, try to use full paths and pwd to avoid errors."""

CODEACT_EXAMPLE = """Here is an example of how you can interact with the environment for task solving:

--- START OF EXAMPLE ---

USER: Create a list of numbers from 1 to 10, and display them in a web page at port 5000.

ASSISTANT:
Sure! Let me create a Python file `app.py`:
<execute_ipython>
create_file('app.py')
</execute_ipython>

USER:
OBSERVATION:
[File: /workspace/app.py (1 lines total)]
(this is the beginning of the file)
1|
(this is the end of the file)
[File app.py created.]

ASSISTANT:
Now I will write the Python code for starting a web server and save it to the file `app.py`:
<execute_ipython>
EDITED_CODE=\"\"\"from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    numbers = list(range(1, 11))
    return str(numbers)

if __name__ == '__main__':
    app.run(port=5000)\"\"\"

insert_content_at_line(
  'app.py',
  1,
  EDITED_CODE,
)
</execute_ipython>

USER:
OBSERVATION:
(this is the beginning of the file)
1|from flask import Flask
2|app = Flask(__name__)
3|
4|@app.route('/')
5|def index():
6|    numbers = list(range(1, 11))
7|    return str(numbers)
8|
9|if __name__ == '__main__':
10|    app.run(port=5000)
(this is the end of the file)
[File updated (edited at line 1). Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]

ASSISTANT:
I have created a Python file `app.py` that will display a list of numbers from 1 to 10 when you run it. Let me run the Python file for you:
<execute_bash>
python3 app.py > server.log 2>&1 &
</execute_bash>

USER:
OBSERVATION:
[1] 121[1]+  Exit 1                  python3 app.py > server.log 2>&1

ASSISTANT: Looks like the server is running with PID 121 then crashed. Let me check the server log:
<execute_bash>
cat server.log
</execute_bash>

USER:
OBSERVATION:
Traceback (most recent call last):
  File "/workspace/app.py", line 2, in <module>
    from flask import Flask
ModuleNotFoundError: No module named 'flask'

ASSISTANT:
It seems that Flask is not installed. Let me install Flask for you:
<execute_bash>
pip install flask
</execute_bash>

USER:
OBSERVATION:
Defaulting to user installation because normal site-packages is not writeable
Collecting flask
  Using cached flask-3.0.3-py3-none-any.whl (101 kB)
Collecting blinker>=1.6.2
  Using cached blinker-1.7.0-py3-none-any.whl (13 kB)
Collecting Werkzeug>=3.0.0
  Using cached werkzeug-3.0.2-py3-none-any.whl (226 kB)
Collecting click>=8.1.3
  Using cached click-8.1.7-py3-none-any.whl (97 kB)
Collecting itsdangerous>=2.1.2
  Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Requirement already satisfied: Jinja2>=3.1.2 in /home/opendevin/.local/lib/python3.10/site-packages (from flask) (3.1.3)
Requirement already satisfied: MarkupSafe>=2.0 in /home/opendevin/.local/lib/python3.10/site-packages (from Jinja2>=3.1.2->flask) (2.1.5)
Installing collected packages: Werkzeug, itsdangerous, click, blinker, flask
Successfully installed Werkzeug-3.0.2 blinker-1.7.0 click-8.1.7 flask-3.0.3 itsdangerous-2.2.0

ASSISTANT:
Now that Flask is installed, let me run the Python file again:
<execute_bash>
python3 app.py > server.log 2>&1 &
</execute_bash>

USER:
OBSERVATION:
[1] 124

ASSISTANT:
Let me check the server log again:
<execute_bash>
cat server.log
</execute_bash>

USER:
OBSERVATION:
* Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit

ASSISTANT:
The server is running on port 5000 with PID 124. You can access the list of numbers by visiting http://127.0.0.1:5000. If you have any further questions, feel free to ask!

USER: Now browse the newly started server's homepage and show me the content.

ASSISTANT:
Sure! Let me browse the server's homepage at http://127.0.0.1:5000:
<execute_browse>
Get the content on "http://127.0.0.1:5000"
</execute_browse>

USER:
OBSERVATION:
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

ASSISTANT:
The content of the server's homepage is "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]". If you have any further questions, feel free to ask!

USER: Now kill the server, make it display the numbers in a table format.

ASSISTANT:
Sure! Let me stop the server first:
<execute_bash>
kill 124
</execute_bash>

USER:
OBSERVATION:
[1]+  Terminated              python3 app.py > server.log 2>&1

ASSISTANT:
The server has been stopped. Let me open the Python file and modify it.
<execute_ipython>
open_file('app.py')
</execute_ipython>

USER:
[File: /workspace/app.py (10 lines total)]
(this is the beginning of the file)
1|from flask import Flask
2|app = Flask(__name__)
3|
4|@app.route('/')
5|def index():
6|    numbers = list(range(1, 11))
7|    return str(numbers)
8|
9|if __name__ == '__main__':
10|    app.run(port=5000)
(this is the end of the file)

ASSISTANT:
I should edit the file to display the numbers in a table format. I should include correct indentation. Let me update the file:
<execute_ipython>
edit_file_by_replace(
  'app.py',
  to_replace="    return str(numbers)",
  new_content="    return '<table>' + ''.join([f'<tr><td>{i}</td></tr>' for i in numbers]) + '</table>'",
)
</execute_ipython>

USER:
Observation:
[File: /workspace/app.py (10 lines total after edit)]
(this is the beginning of the file)
1|from flask import Flask
2|app = Flask(__name__)
3|
4|@app.route('/')
5|def index():
6|    numbers = list(range(1, 11))
7|    return '<table>' + ''.join([f'<tr><td>{i}</td></tr>' for i in numbers]) + '</table>'
8|
9|if __name__ == '__main__':
10|    app.run(port=5000)
(this is the end of the file)
[File updated (edited at line 7). Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]

ASSISTANT:
Running the updated file:
<execute_bash>
python3 app.py > server.log 2>&1 &
</execute_bash>

USER:
Observation:
[1] 126

ASSISTANT:
The server is running on port 5000 with PID 126. You can access the list of numbers in a table format by visiting http://127.0.0.1:5000. Let me know if you have any further requests!
<finish></finish>

--- END OF EXAMPLE ---
"""


def test_prompt_manager_without_micro_agent(prompt_dir, agent_skills_docs):
    manager = PromptManager(prompt_dir, agent_skills_docs)

    assert manager.prompt_dir == prompt_dir
    assert manager.agent_skills_docs == agent_skills_docs
    assert manager.micro_agent is None

    assert isinstance(manager.system_message, str)
    assert manager.system_message == CODEACT_SYSTEM_PROMPT
    assert isinstance(manager.initial_user_message, str)
    assert manager.initial_user_message == CODEACT_EXAMPLE + "\n\n\nNOW, LET'S START!"
    assert 'micro_agent' not in manager.initial_user_message


def test_prompt_manager_with_micro_agent(prompt_dir, agent_skills_docs):
    micro_agent_name = 'test_micro_agent'
    micro_agent_content = (
        '## Micro Agent\n'
        'This is a test micro agent.\n'
        'It is used to test the prompt manager.\n'
    )

    # Create a temporary micro agent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(os.path.join(prompt_dir, 'micro', f'{micro_agent_name}.md'), 'w') as f:
        f.write(micro_agent_content)

    manager = PromptManager(prompt_dir, agent_skills_docs, micro_agent_name)

    assert manager.prompt_dir == prompt_dir
    assert manager.agent_skills_docs == agent_skills_docs
    assert manager.micro_agent == micro_agent_content

    assert isinstance(manager.system_message, str)
    assert manager.system_message == CODEACT_SYSTEM_PROMPT

    assert isinstance(manager.initial_user_message, str)
    assert manager.initial_user_message == (
        CODEACT_EXAMPLE
        + '\n\n'
        + '--- BEGIN OF GUIDELINE ---\n'
        + 'The following information may assist you in completing your task:\n\n'
        + micro_agent_content
        + '\n'
        + '--- END OF GUIDELINE ---\n'
        + "\n\nNOW, LET'S START!"
    )

    assert micro_agent_content in manager.initial_user_message

    # Clean up the temporary file
    os.remove(os.path.join(prompt_dir, 'micro', f'{micro_agent_name}.md'))


def test_prompt_manager_file_not_found(prompt_dir, agent_skills_docs):
    with pytest.raises(FileNotFoundError):
        PromptManager(prompt_dir, agent_skills_docs, 'non_existent_micro_agent')


def test_prompt_manager_template_rendering(prompt_dir, agent_skills_docs):
    # Create temporary template files
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write('System prompt: {{ agent_skills_docs }}')
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt: {{ micro_agent }}')

    manager = PromptManager(prompt_dir, agent_skills_docs)

    assert manager.system_message == f'System prompt: {agent_skills_docs}'
    assert manager.initial_user_message == 'User prompt: None'

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'system_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))
