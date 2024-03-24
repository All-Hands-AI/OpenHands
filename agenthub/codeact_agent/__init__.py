import os
import re
from litellm import completion
from termcolor import colored
from typing import List, Dict

from opendevin.agent import Agent, Message, Role
from opendevin.lib.event import Event
from opendevin.lib.command_manager import CommandManager
from opendevin.sandbox.sandbox import DockerInteractive

assert (
    "OPENAI_API_KEY" in os.environ
), "Please set the OPENAI_API_KEY environment variable."



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


class CodeActAgent(Agent):
    def __init__(
        self,
        instruction: str,
        workspace_dir: str,
        model_name: str,
        max_steps: int = 100
    ) -> None:
        """
        Initializes a new instance of the CodeActAgent class.

        Parameters:
        - instruction (str): The instruction for the agent to execute.
        - max_steps (int): The maximum number of steps to run the agent.
        """
        super().__init__(instruction, workspace_dir, model_name, max_steps)
        self._history = [Message(Role.SYSTEM, SYSTEM_MESSAGE)]
        self._history.append(Message(Role.USER, instruction))
        self.env = DockerInteractive(workspace_dir=workspace_dir)
        print(colored("===USER:===\n" + instruction, "green"))

    def _history_to_messages(self) -> List[Dict]:
        return [message.to_dict() for message in self._history]

    def run(self) -> None:
        """
        Starts the execution of the assigned instruction. This method should
        be implemented by subclasses to define the specific execution logic.
        """
        for _ in range(self.max_steps):
            response = completion(
                messages=self._history_to_messages(),
                model=self.model_name,
                stop=["</execute>"],
                temperature=0.0,
                seed=42,
            )
            action = parse_response(response)
            self._history.append(Message(Role.ASSISTANT, action))
            print(colored("===ASSISTANT:===\n" + action, "yellow"))

            command = re.search(r"<execute>(.*)</execute>", action, re.DOTALL)
            if command is not None:
                # a command was found
                command_group = command.group(1)
                if command_group.strip() == "exit":
                    print(colored("Exit received. Exiting...", "red"))
                    break
                # execute the code
                # TODO: does exit_code get loaded into Message?
                exit_code, observation = self.env.execute(command_group)
                self._history.append(Message(Role.ASSISTANT, observation))
                print(colored("===ENV OBSERVATION:===\n" + observation, "blue"))
            else:
                # we could provide a error message for the model to continue similar to
                # https://github.com/xingyaoww/mint-bench/blob/main/mint/envs/general_env.py#L18-L23
                observation = INVALID_INPUT_MESSAGE
                self._history.append(Message(Role.ASSISTANT, observation))
                print(colored("===ENV OBSERVATION:===\n" + observation, "blue"))

        self.env.close()

    def chat(self, message: str) -> None:
        """
        Optional method for interactive communication with the agent during its execution. Implementations
        can use this method to modify the agent's behavior or state based on chat inputs.

        Parameters:
        - message (str): The chat message or command.
        """
        raise NotImplementedError

    # TODO: implement these abstract methods
    def add_event(self, event: Event) -> None:
        raise NotImplementedError("Implement this abstract method")

    def step(self, cmd_mgr: CommandManager) -> Event:
        raise NotImplementedError("Implement this abstract method")

    def search_memory(self, query: str) -> List[str]:
        raise NotImplementedError("Implement this abstract method")


Agent.register("CodeActAgent", CodeActAgent)
