from functools import partial

from openhands.agenthub.codeact_agent import CodeActAgent
from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.agenthub.loc_agent.function_calling import (
    convert_tool_call_to_action,
)
from openhands.agenthub.loc_agent.function_calling import (
    get_tools as get_loc_agent_tools,
)
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM


class LocAgent(CodeActAgent):
    VERSION = '1.0'

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the LocAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for the agent
        """
        super().__init__(llm, config)

        self.tools = get_loc_agent_tools()
        logger.debug(
            f"TOOLS loaded for LocAgent: {', '.join([tool.get('function').get('name') for tool in self.tools])}"
        )
        self.response_to_actions = partial(
            response_to_actions,
            convert_tool_call_to_action=convert_tool_call_to_action,
        )
