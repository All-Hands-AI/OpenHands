from typing import TypedDict

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.schema import AgentState
from openhands.events.action import (
    Action,
    AgentFinishAction,
    AgentRejectAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    MessageAction,
)
from openhands.events.observation import (
    AgentStateChangedObservation,
    BrowserOutputObservation,
    CmdOutputMetadata,
    CmdOutputObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.events.serialization.event import event_to_dict
from openhands.llm.llm import LLM

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_ext.tools.mcp import SseServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent

"""
FIXME: There are a few problems this surfaced
* FileWrites seem to add an unintended newline at the end of the file
* Browser not working
"""


class DummyAgent(Agent):
    VERSION = '1.0'
    """
    The DummyAgent is used for e2e testing. It just sends the same set of actions deterministically,
    without making any LLM calls.
    """

    def __init__(self, llm: LLM, config: AgentConfig, workspace_mount_path_in_sandbox_store_in_session: bool = True,):
        super().__init__(llm, config)

        """Initialize async components of the agent"""
        tools = []
        # for tool_url in ["http://15.235.225.246:4010/sse"]:
        #     for tool in await mcp_server_tools(SseServerParams(url=tool_url)):
        #         tools.append(tool)

        print(f"tools used: {tools}")

        model_client = AnthropicChatCompletionClient(model=llm.config.model, api_key=llm.config.api_key.get_secret_value())
        print(f"model_client: {llm.config.api_key.get_secret_value()}")
        mcp = AssistantAgent(name="MCPTools", model_client=model_client, tools=tools)
        self.team = MagenticOneGroupChat(participants=[mcp], model_client=model_client)

        self.steps: list[Action] = [
            MessageAction('Time to get started!'),
            CmdRunAction(command='echo "foo"'),
            FileWriteAction(
                content='echo "Hello, World!"', path='hello.sh'
            ),
            FileReadAction(path='hello.sh'),
            AgentFinishAction(
                outputs={}, thought='Task completed', action='finish'
            ),
        ]

    async def step(self, state: State) -> Action:
        task = state.get_last_user_message().content
        result = None
        await self.team.reset()
        print(f"task: {task}")
        async for message in self.team.run_stream(
            task=task
        ):
            print(f"step result: {message}")
            result = message

        return AgentFinishAction(final_thought=result.messages[0].to_model_text())
