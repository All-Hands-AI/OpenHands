import os
import re
import argparse
from litellm import completion
from termcolor import colored

from opendevin.sandbox.docker import DockerInteractive

assert (
    "OPENAI_API_KEY" in os.environ
), "Please set the OPENAI_API_KEY environment variable."

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model", type=str, default="gpt-3.5-turbo-0125", help="The model to use."
)
parser.add_argument(
    "--max_turns", type=int, default=10, help="The maximum number of turns."
)
args = parser.parse_args()

SYSTEM_MESSAGE = """You are a helpful assistant. You will be provided access (as root) to a bash shell to complete user-provided tasks.
You will be able to execute commands in the bash shell, interact with the file system, install packages, and receive the output of your commands.

DO NOT provide code in ```triple backticks```. Instead, you should execute bash command on behalf of the user by wrapping them with <execute> and </execute>.
For example:

You can list the files in the current directory by executing the following command:
<execute>ls</execute>

You can also install packages using pip:
<execute> pip install numpy </execute>

You can also write a block of code to a file:
<execute>
echo "import math
print(math.pi)" > math.py
</execute>

When you are done, execute "exit" to close the shell and end the conversation.
"""

INVALID_INPUT_MESSAGE = (
    "I don't understand your input. \n"
    "If you want to execute command, please use <execute> YOUR_COMMAND_HERE </execute>.\n"
    "If you already completed the task, please exit the shell by generating: <execute> exit </execute>."
)


def parse_response(response) -> str:
    action = response.choices[0].message.content
    if "<execute>" in action and "</execute>" not in action:
        action += "</execute>"
    return action


# docker build -f opendevin/sandbox/Dockerfile -t opendevin-sandbox .
env = DockerInteractive("opendevin-sandbox:latest")

messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
user_input = "Please write a flask app that returns 'Hello, World!' at the root URL, then start the app on port 5000. `python3` has already been installed for you."
messages.append({"role": "user", "content": user_input})
print(colored("===USER:===\n" + user_input, "green"))

for _ in range(args.max_turns):
    response = completion(
        messages=messages,
        model=args.model,
        stop=["</execute>"],
        temperature=0.0,
        seed=42,
    )
    action = parse_response(response)
    messages.append({"role": "assistant", "content": action})
    print(colored("===ASSISTANT:===\n" + action, "yellow"))

    command = re.search(r"<execute>(.*)</execute>", action, re.DOTALL)
    if command is not None:
        # a command was found
        command = command.group(1)
        if command.strip() == "exit":
            print(colored("Exit received. Exiting...", "red"))
            break
        # execute the code
        observation = env.execute(command)
        messages.append({"role": "assistant", "content": observation})
        print(colored("===ENV OBSERVATION:===\n" + observation, "blue"))
    else:
        # we could provide a error message for the model to continue similar to
        # https://github.com/xingyaoww/mint-bench/blob/main/mint/envs/general_env.py#L18-L23
        observation = INVALID_INPUT_MESSAGE
        messages.append({"role": "assistant", "content": observation})
        print(colored("===ENV OBSERVATION:===\n" + observation, "blue"))

env.close()
