import os

import openhands.agenthub.task_solving_agent.function_calling as task_solving_function_calling
from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentFinishAction,
)
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


class TaskSolvingAgent(CodeActAgent):
    VERSION = '1.0'
    """
    This Agent wraps the CodeAct agent with prompt adjustments for general task solving.
    """

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the TaskSolvingAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        """
        super().__init__(llm, config)

        # Get codeact tools
        self.tools = self._get_tools()

        # Specilized tools for planning
        specilized_tools = task_solving_function_calling.get_tools()

        # Override tools with the same name
        for specialized_tool in specilized_tools:
            is_found = False
            for i, tool in enumerate(self.tools):
                if tool['function']['name'] == specialized_tool['function']['name']:
                    self.tools[i] = specialized_tool
                    is_found = True
                    break
            if not is_found:
                self.tools.append(specialized_tool)

        # Override prompt_manager to use task-solving-specific prompts
        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )

        # Override the conversation memory to use task-solving-specific prompts
        self.conversation_memory = ConversationMemory(self.config, self.prompt_manager)

    def step(self, state: State) -> Action:
        """Performs one step using the CodeAct Agent.

        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        # Continue with pending actions if any
        if self.pending_actions:
            return self.pending_actions.popleft()

        # if we're done, go back
        latest_user_message = state.get_last_user_message()
        if latest_user_message and latest_user_message.content.strip() == '/exit':
            return AgentFinishAction()

        # Condense the events from the state. If we get a view we'll pass those
        # to the conversation manager for processing, but if we get a condensation
        # event we'll just return that instead of an action. The controller will
        # immediately ask the agent to step again with the new view.
        condensed_history: list[Event] = []
        match self.condenser.condensed_history(state):
            case View(events=events):
                condensed_history = events

            case Condensation(action=condensation_action):
                return condensation_action

        logger.debug(
            f'Processing {len(condensed_history)} events from a total of {len(state.history)} events'
        )

        messages = self._get_messages(condensed_history)
        params: dict = {
            'messages': self.llm.format_messages_for_llm(messages),
        }
        params['tools'] = self.tools

        if self.mcp_tools and self.config.enable_mcp_tools:
            # Only add tools with unique names
            existing_names = {tool['function']['name'] for tool in params['tools']}
            unique_mcp_tools = [
                tool
                for tool in self.mcp_tools
                if tool['function']['name'] not in existing_names
            ]
            params['tools'] += unique_mcp_tools

        # import json
        # logger.warning(f'TaskSolvingAgent messages:\n{json.dumps(params["messages"], indent=2)}')

        # log to litellm proxy if possible
        params['extra_body'] = {'metadata': state.to_llm_metadata(agent_name=self.name)}
        response = self.llm.completion(**params)
        logger.debug(f'Response from LLM: {response}')
        actions = task_solving_function_calling.response_to_actions(response)
        logger.debug(f'Actions after response_to_actions: {actions}')
        for action in actions:
            self.pending_actions.append(action)
        return self.pending_actions.popleft()
