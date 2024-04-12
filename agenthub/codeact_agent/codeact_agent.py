import re
from typing import List, Mapping

from opendevin.action import (
    Action,
    AgentEchoAction,
    AgentFinishAction,
    CmdRunAction,
)
from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.observation import (
    AgentMessageObservation,
    CmdOutputObservation,
)
from opendevin.parse_commands import parse_command_file
from opendevin.state import State

COMMAND_DOCS = parse_command_file()
COMMAND_SEGMENT = (
    f"""

Apart from the standard bash commands, you can also use the following special commands:
{COMMAND_DOCS}
"""
    if COMMAND_DOCS is not None
    else ""
)
SYSTEM_MESSAGE = f"""You are a helpful assistant. You will be provided access (as root) to a bash shell to complete user-provided tasks.
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
{COMMAND_SEGMENT}

When you are done, execute the following to close the shell and end the conversation:
<execute>exit</execute> 
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
    """
    The Code Act Agent is a minimalist agent. 
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.
    """
    
    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.messages: List[Mapping[str, str]] = []

    def step(self, state: State) -> Action:
        """
        Performs one step using the Code Act Agent. 
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info and background commands

        Returns:
        - CmdRunAction(command) - command action to run
        - AgentEchoAction(content=INVALID_INPUT_MESSAGE) - invalid command output

        Raises:
        - NotImplementedError - for actions other than CmdOutputObservation or AgentMessageObservation
        """

        if len(self.messages) == 0:
            assert state.plan.main_goal, "Expecting instruction to be set"
            self.messages = [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": state.plan.main_goal},
            ]
        updated_info = state.updated_info
        if updated_info:
            for prev_action, obs in updated_info:
                assert isinstance(
                    prev_action, (CmdRunAction, AgentEchoAction)
                ), "Expecting CmdRunAction or AgentEchoAction for Action"
                if isinstance(
                    obs, AgentMessageObservation
                ):  # warning message from itself
                    self.messages.append({"role": "user", "content": obs.content})
                elif isinstance(obs, CmdOutputObservation):
                    content = "OBSERVATION:\n" + obs.content
                    content += f"\n[Command {obs.command_id} finished with exit code {obs.exit_code}]]"
                    self.messages.append({"role": "user", "content": content})
                else:
                    raise NotImplementedError(
                        f"Unknown observation type: {obs.__class__}"
                    )
        response = self.llm.completion(
            messages=self.messages,
            stop=["</execute>"],
            temperature=0.0
        )
        action_str: str = parse_response(response)
        self.messages.append({"role": "assistant", "content": action_str})

        command = re.search(r"<execute>(.*)</execute>", action_str, re.DOTALL)
        if command is not None:
            # a command was found
            command_group = command.group(1)
            if command_group.strip() == "exit":
                return AgentFinishAction()
            return CmdRunAction(command=command_group)
            # # execute the code
            # # TODO: does exit_code get loaded into Message?
            # exit_code, observation = self.env.execute(command_group)
            # self._history.append(Message(Role.ASSISTANT, observation))
        else:
            # we could provide a error message for the model to continue similar to
            # https://github.com/xingyaoww/mint-bench/blob/main/mint/envs/general_env.py#L18-L23
            # observation = INVALID_INPUT_MESSAGE
            # self._history.append(Message(Role.ASSISTANT, observation))
            return AgentEchoAction(
                content=INVALID_INPUT_MESSAGE
            )  # warning message to itself

    def search_memory(self, query: str) -> List[str]:
        raise NotImplementedError("Implement this abstract method")
