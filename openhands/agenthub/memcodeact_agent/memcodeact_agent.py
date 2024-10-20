import os
from itertools import islice

from openhands.agenthub.memcodeact_agent.action_parser import MemCodeActResponseParser
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
    UserRejectObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.observation import Observation
from openhands.events.serialization.event import truncate_content
from openhands.llm.llm import LLM
from openhands.memory.condenser import MemoryCondenser
from openhands.memory.conversation_memory import ConversationMemory
from openhands.memory.core_memory import CoreMemory
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from openhands.utils.microagent import MicroAgent
from openhands.utils.prompt import PromptManager


class MemCodeActAgent(Agent):
    VERSION = '1.9'
    """
    The MemCode Act Agent is a memory-enabled version of the CodeAct agent.

    Its memory modules are:
    - conversation: easy to recall memory (history)
    - core: core system messages
    - long_term: long-term memory

    Its memory actions are:
        - "core_memory_append"
        - "core_memory_replace"
        - "conversation_search"
        - "long_term_memory_insert"
        - "long_term_memory_search"
        - "summarize_conversation"
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.

    ### Overview

    This agent implements:
    - the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a unified **code** action space for both *simplicity* and *performance* (see paper for more details).
    - inspired by the Generative Agents idea([paper](https://arxiv.org/abs/2304.03442)) and the MemGPT idea ([paper](https://arxiv.org/abs/2310.08560))

    The conceptual idea is illustrated below. At each turn, the agent can:

    1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
    2. **CodeAct**: Choose to perform the task by executing code
        - Execute any valid Linux `bash` command
        - Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.
    3. **MemGPT**: Manage its own memory
        - truncate its history and replace it with a summary
        - store information in its long-term memory
        - search for information relevant to the task.

    """

    sandbox_plugins: list[PluginRequirement] = [
        # NOTE: AgentSkillsRequirement need to go before JupyterRequirement, since
        # AgentSkillsRequirement provides a lot of Python functions,
        # and it needs to be initialized before Jupyter for Jupyter to use those functions.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]

    action_parser = MemCodeActResponseParser()

    # NOTE: memory includes 'conversation' and 'core' memory blocks
    conversation_memory: ConversationMemory
    core_memory: CoreMemory

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the MemCodeActAgent class.

        Parameters:
        - llm: The LLM to be used by this agent
        - config: The agent configuration
        """
        super().__init__(llm, config)

        self.memory_config = llm.config  # TODO this should be MemoryConfig

        self.micro_agent = (
            MicroAgent(
                os.path.join(
                    os.path.dirname(__file__), 'micro', f'{config.micro_agent_name}.md'
                )
            )
            if config.micro_agent_name
            else None
        )

        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__)),
            agent_skills_docs=AgentSkillsRequirement.documentation,
            micro_agent=self.micro_agent,
        )

    def action_to_str(self, action: Action) -> str:
        if isinstance(action, CmdRunAction):
            return (
                f'{action.thought}\n<execute_bash>\n{action.command}\n</execute_bash>'
            )
        elif isinstance(action, IPythonRunCellAction):
            return f'{action.thought}\n<execute_ipython>\n{action.code}\n</execute_ipython>'
        elif isinstance(action, AgentDelegateAction):
            return f'{action.thought}\n<execute_browse>\n{action.inputs["task"]}\n</execute_browse>'
        elif isinstance(action, MessageAction):
            return action.content
        elif isinstance(action, AgentFinishAction) and action.source == 'agent':
            return action.thought
        return ''

    def get_action_message(self, action: Action) -> Message | None:
        if (
            isinstance(action, AgentDelegateAction)
            or isinstance(action, CmdRunAction)
            or isinstance(action, IPythonRunCellAction)
            or isinstance(action, MessageAction)
            or (isinstance(action, AgentFinishAction) and action.source == 'agent')
        ):
            content = [TextContent(text=self.action_to_str(action))]

            if (
                self.llm.vision_is_active()
                and isinstance(action, MessageAction)
                and action.images_urls
            ):
                content.append(ImageContent(image_urls=action.images_urls))

            return Message(
                role='user' if action.source == 'user' else 'assistant', content=content
            )
        return None

    def get_observation_message(self, obs: Observation) -> Message | None:
        max_message_chars = self.llm.config.max_message_chars
        obs_prefix = 'OBSERVATION:\n'
        if isinstance(obs, CmdOutputObservation):
            text = obs_prefix + truncate_content(obs.content, max_message_chars)
            text += (
                f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]'
            )
            return Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, IPythonRunCellObservation):
            text = obs_prefix + obs.content
            # replace base64 images with a placeholder
            splitted = text.split('\n')
            for i, line in enumerate(splitted):
                if '![image](data:image/png;base64,' in line:
                    splitted[i] = (
                        '![image](data:image/png;base64, ...) already displayed to user'
                    )
            text = '\n'.join(splitted)
            text = truncate_content(text, max_message_chars)
            return Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, AgentDelegateObservation):
            text = obs_prefix + truncate_content(
                obs.outputs['content'] if 'content' in obs.outputs else '',
                max_message_chars,
            )
            return Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, ErrorObservation):
            text = obs_prefix + truncate_content(obs.content, max_message_chars)
            text += '\n[Error occurred in processing last action]'
            return Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, UserRejectObservation):
            text = 'OBSERVATION:\n' + truncate_content(obs.content, max_message_chars)
            text += '\n[Last action has been rejected by the user]'
            return Message(role='user', content=[TextContent(text=text)])
        else:
            # If an observation message is not returned, it will cause an error
            # when the LLM tries to return the next message
            logger.debug(f'Unknown observation type: {type(obs)}')
            return None

    def reset(self) -> None:
        """Resets the MemCodeAct Agent."""
        super().reset()

        # reset the memory modules
        self.core_memory.reset()
        self.conversation_memory.reset()

    def step(self, state: State) -> Action:
        """Performs one step using the MemCodeAct Agent.
        This includes gathering info on previous steps and prompting the model to make an action to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - SummarizeAction() - summarize the conversation
        - RecallAction() - search the agent's history
        - LongTermMemoryInsertAction() - archive information in the long-term memory
        - LongTermMemorySearchAction() - search the agent's long-term memory
        - AgentFinishAction() - end the interaction
        """
        # if we're done, go back
        last_user_message = state.get_last_user_message()
        if last_user_message and last_user_message.strip() == '/exit':
            return AgentFinishAction()

        # initialize the memory modules

        # stores and searches the agent's long-term memory (vector store)
        # long_term_memory = LongTermMemory(llm_config=memory_config, agent_config=config, event_stream=self.event_stream)

        # stores and recalls the whole agent's history
        assert self.memory_config is not None

        # update conversation memory for this step
        if not hasattr(self, 'conversation_memory') or not self.conversation_memory:
            self.conversation_memory = ConversationMemory(
                memory_config=self.memory_config, state=state
            )
        else:
            self.conversation_memory.update(state)

        # initialize core memory
        if not hasattr(self, 'core_memory') or not self.core_memory:
            self.core_memory = CoreMemory(limit=1500)

        # prepare what we want to send to the LLM
        messages = self._get_messages(self.conversation_memory.history, state)
        params = {
            'messages': self.llm.format_messages_for_llm(messages),
            'stop': [
                '</execute_ipython>',
                '</execute_bash>',
                '</execute_browse>',
            ],
        }

        response = self.llm.completion(**params)

        return self.action_parser.parse(response)

    def _get_messages(self, history: list[Event], state: State) -> list[Message]:
        messages: list[Message] = [
            Message(
                role='system',
                content=[
                    TextContent(
                        text=self.prompt_manager.system_message,
                        cache_prompt=self.llm.is_caching_prompt_active(),  # Cache system prompt
                    )
                ],
            ),
            Message(
                role='user',
                content=[
                    TextContent(
                        text=self.prompt_manager.initial_user_message,
                        cache_prompt=self.llm.is_caching_prompt_active(),  # if the user asks the same query,
                    )
                ],
            ),
        ]

        for event in history:
            # create a regular message from an event
            if isinstance(event, Action):
                message = self.get_action_message(event)
            elif isinstance(event, Observation):
                message = self.get_observation_message(event)
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            # add regular message
            if message:
                # handle error if the message is the SAME role as the previous message
                # litellm.exceptions.BadRequestError: litellm.BadRequestError: OpenAIException - Error code: 400 - {'detail': 'Only supports u/a/u/a/u...'}
                # there shouldn't be two consecutive messages from the same role
                if messages and messages[-1].role == message.role:
                    messages[-1].content.extend(message.content)
                else:
                    messages.append(message)

        # Add caching to the last 2 user messages
        if self.llm.is_caching_prompt_active():
            user_turns_processed = 0
            for message in reversed(messages):
                if message.role == 'user' and user_turns_processed < 2:
                    message.content[
                        -1
                    ].cache_prompt = True  # Last item inside the message content
                    user_turns_processed += 1

        # The latest user message is important:
        # we want to remind the agent of the environment constraints
        latest_user_message = next(
            islice(
                (
                    m
                    for m in reversed(messages)
                    if m.role == 'user'
                    and any(isinstance(c, TextContent) for c in m.content)
                ),
                1,
            ),
            None,
        )
        if latest_user_message:
            reminder_text = f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>.'
            latest_user_message.content.append(TextContent(text=reminder_text))

        return messages

    def summarize_messages_inplace(self, state: State):
        """Summarizes the earlier messages in the agent's memory to reduce token usage. Uses memGPT's algorithm for in-place summarization."""
        if len(self.conversation_memory.history) <= 2:
            return

        # summarize the conversation history using the condenser
        # conversation_memory.history will include the previous summary, if any, while the regular state.history does not
        condenser = MemoryCondenser(self.llm)
        messages = self._get_messages(self.conversation_memory.history, state)
        summary = condenser.condense(messages)

        logger.debug(f'Summarized conversation history to: {summary}')
