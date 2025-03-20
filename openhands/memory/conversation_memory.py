from litellm import ModelResponse

from openhands.core.config.agent_config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import ImageContent, Message, TextContent
from openhands.core.schema import ActionType
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentThinkAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.event import Event, RecallType
from openhands.events.observation import (
    AgentCondensationObservation,
    AgentDelegateObservation,
    AgentThinkObservation,
    BrowserOutputObservation,
    CmdOutputObservation,
    FileEditObservation,
    FileReadObservation,
    IPythonRunCellObservation,
    UserRejectObservation,
)
from openhands.events.observation.agent import (
    MicroagentKnowledge,
    RecallObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.observation import Observation
from openhands.events.serialization.event import truncate_content
from openhands.utils.prompt import PromptManager, RepositoryInfo, RuntimeInfo


class ConversationMemory:
    """Processes event history into a coherent conversation for the agent."""

    def __init__(self, config: AgentConfig, prompt_manager: PromptManager):
        self.agent_config = config
        self.prompt_manager = prompt_manager

    def process_events(
        self,
        condensed_history: list[Event],
        initial_messages: list[Message],
        max_message_chars: int | None = None,
        vision_is_active: bool = False,
    ) -> list[Message]:
        """Process state history into a list of messages for the LLM.

        Ensures that tool call actions are processed correctly in function calling mode.

        Args:
            condensed_history: The condensed history of events to convert
            initial_messages: The initial messages to include in the conversation
            max_message_chars: The maximum number of characters in the content of an event included
                in the prompt to the LLM. Larger observations are truncated.
            vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included.
        """

        events = condensed_history

        # log visual browsing status
        logger.debug(f'Visual browsing: {self.agent_config.enable_som_visual_browsing}')

        # Process special events first (system prompts, etc.)
        messages = initial_messages

        # Process regular events
        pending_tool_call_action_messages: dict[str, Message] = {}
        tool_call_id_to_message: dict[str, Message] = {}

        for i, event in enumerate(events):
            # create a regular message from an event
            if isinstance(event, Action):
                messages_to_add = self._process_action(
                    action=event,
                    pending_tool_call_action_messages=pending_tool_call_action_messages,
                    vision_is_active=vision_is_active,
                )
            elif isinstance(event, Observation):
                messages_to_add = self._process_observation(
                    obs=event,
                    tool_call_id_to_message=tool_call_id_to_message,
                    max_message_chars=max_message_chars,
                    vision_is_active=vision_is_active,
                    enable_som_visual_browsing=self.agent_config.enable_som_visual_browsing,
                    current_index=i,
                    events=events,
                )
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            # Check pending tool call action messages and see if they are complete
            _response_ids_to_remove = []
            for (
                response_id,
                pending_message,
            ) in pending_tool_call_action_messages.items():
                assert pending_message.tool_calls is not None, (
                    'Tool calls should NOT be None when function calling is enabled & the message is considered pending tool call. '
                    f'Pending message: {pending_message}'
                )
                if all(
                    tool_call.id in tool_call_id_to_message
                    for tool_call in pending_message.tool_calls
                ):
                    # If complete:
                    # -- 1. Add the message that **initiated** the tool calls
                    messages_to_add.append(pending_message)
                    # -- 2. Add the tool calls **results***
                    for tool_call in pending_message.tool_calls:
                        messages_to_add.append(tool_call_id_to_message[tool_call.id])
                        tool_call_id_to_message.pop(tool_call.id)
                    _response_ids_to_remove.append(response_id)
            # Cleanup the processed pending tool messages
            for response_id in _response_ids_to_remove:
                pending_tool_call_action_messages.pop(response_id)

            messages += messages_to_add

        return messages

    def process_initial_messages(self, with_caching: bool = False) -> list[Message]:
        """Create the initial messages for the conversation."""
        return [
            Message(
                role='system',
                content=[
                    TextContent(
                        text=self.prompt_manager.get_system_message(),
                        cache_prompt=with_caching,
                    )
                ],
            )
        ]

    def _process_action(
        self,
        action: Action,
        pending_tool_call_action_messages: dict[str, Message],
        vision_is_active: bool = False,
    ) -> list[Message]:
        """Converts an action into a message format that can be sent to the LLM.

        This method handles different types of actions and formats them appropriately:
        1. For tool-based actions (AgentDelegate, CmdRun, IPythonRunCell, FileEdit) and agent-sourced AgentFinish:
            - In function calling mode: Stores the LLM's response in pending_tool_call_action_messages
            - In non-function calling mode: Creates a message with the action string
        2. For MessageActions: Creates a message with the text content and optional image content

        Args:
            action: The action to convert. Can be one of:
                - CmdRunAction: For executing bash commands
                - IPythonRunCellAction: For running IPython code
                - FileEditAction: For editing files
                - FileReadAction: For reading files using openhands-aci commands
                - BrowseInteractiveAction: For browsing the web
                - AgentFinishAction: For ending the interaction
                - MessageAction: For sending messages

            pending_tool_call_action_messages: Dictionary mapping response IDs to their corresponding messages.
                Used in function calling mode to track tool calls that are waiting for their results.

            vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included

        Returns:
            list[Message]: A list containing the formatted message(s) for the action.
                May be empty if the action is handled as a tool call in function calling mode.

        Note:
            In function calling mode, tool-based actions are stored in pending_tool_call_action_messages
            rather than being returned immediately. They will be processed later when all corresponding
            tool call results are available.
        """
        # create a regular message from an event
        if isinstance(
            action,
            (
                AgentDelegateAction,
                AgentThinkAction,
                IPythonRunCellAction,
                FileEditAction,
                FileReadAction,
                BrowseInteractiveAction,
                BrowseURLAction,
            ),
        ) or (isinstance(action, CmdRunAction) and action.source == 'agent'):
            tool_metadata = action.tool_call_metadata
            assert tool_metadata is not None, (
                'Tool call metadata should NOT be None when function calling is enabled. Action: '
                + str(action)
            )

            llm_response: ModelResponse = tool_metadata.model_response
            assistant_msg = getattr(llm_response.choices[0], 'message')

            # Add the LLM message (assistant) that initiated the tool calls
            # (overwrites any previous message with the same response_id)
            logger.debug(
                f'Tool calls type: {type(assistant_msg.tool_calls)}, value: {assistant_msg.tool_calls}'
            )
            pending_tool_call_action_messages[llm_response.id] = Message(
                role=getattr(assistant_msg, 'role', 'assistant'),
                # tool call content SHOULD BE a string
                content=[TextContent(text=assistant_msg.content or '')]
                if assistant_msg.content is not None
                else [],
                tool_calls=assistant_msg.tool_calls,
            )
            return []
        elif isinstance(action, AgentFinishAction):
            role = 'user' if action.source == 'user' else 'assistant'

            # when agent finishes, it has tool_metadata
            # which has already been executed, and it doesn't have a response
            # when the user finishes (/exit), we don't have tool_metadata
            tool_metadata = action.tool_call_metadata
            if tool_metadata is not None:
                # take the response message from the tool call
                assistant_msg = getattr(
                    tool_metadata.model_response.choices[0], 'message'
                )
                content = assistant_msg.content or ''

                # save content if any, to thought
                if action.thought:
                    if action.thought != content:
                        action.thought += '\n' + content
                else:
                    action.thought = content

                # remove the tool call metadata
                action.tool_call_metadata = None
            if role not in ('user', 'system', 'assistant', 'tool'):
                raise ValueError(f'Invalid role: {role}')
            return [
                Message(
                    role=role,  # type: ignore[arg-type]
                    content=[TextContent(text=action.thought)],
                )
            ]
        elif isinstance(action, MessageAction):
            role = 'user' if action.source == 'user' else 'assistant'
            content = [TextContent(text=action.content or '')]
            if vision_is_active and action.image_urls:
                content.append(ImageContent(image_urls=action.image_urls))
            if role not in ('user', 'system', 'assistant', 'tool'):
                raise ValueError(f'Invalid role: {role}')
            return [
                Message(
                    role=role,  # type: ignore[arg-type]
                    content=content,
                )
            ]
        elif isinstance(action, CmdRunAction) and action.source == 'user':
            content = [
                TextContent(text=f'User executed the command:\n{action.command}')
            ]
            return [
                Message(
                    role='user',  # Always user for CmdRunAction
                    content=content,
                )
            ]
        return []

    def _process_observation(
        self,
        obs: Observation,
        tool_call_id_to_message: dict[str, Message],
        max_message_chars: int | None = None,
        vision_is_active: bool = False,
        enable_som_visual_browsing: bool = False,
        current_index: int = 0,
        events: list[Event] | None = None,
    ) -> list[Message]:
        """Converts an observation into a message format that can be sent to the LLM.

        This method handles different types of observations and formats them appropriately:
        - CmdOutputObservation: Formats command execution results with exit codes
        - IPythonRunCellObservation: Formats IPython cell execution results, replacing base64 images
        - FileEditObservation: Formats file editing results
        - FileReadObservation: Formats file reading results from openhands-aci
        - AgentDelegateObservation: Formats results from delegated agent tasks
        - ErrorObservation: Formats error messages from failed actions
        - UserRejectObservation: Formats user rejection messages

        In function calling mode, observations with tool_call_metadata are stored in
        tool_call_id_to_message for later processing instead of being returned immediately.

        Args:
            obs: The observation to convert
            tool_call_id_to_message: Dictionary mapping tool call IDs to their corresponding messages (used in function calling mode)
            max_message_chars: The maximum number of characters in the content of an observation included in the prompt to the LLM
            vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included
            enable_som_visual_browsing: Whether to enable visual browsing for the SOM model
            current_index: The index of the current event in the events list (for deduplication)
            events: The list of all events (for deduplication)

        Returns:
            list[Message]: A list containing the formatted message(s) for the observation.
                May be empty if the observation is handled as a tool response in function calling mode.

        Raises:
            ValueError: If the observation type is unknown
        """
        message: Message

        if isinstance(obs, CmdOutputObservation):
            # if it doesn't have tool call metadata, it was triggered by a user action
            if obs.tool_call_metadata is None:
                text = truncate_content(
                    f'\nObserved result of command executed by user:\n{obs.to_agent_observation()}',
                    max_message_chars,
                )
            else:
                text = truncate_content(obs.to_agent_observation(), max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, IPythonRunCellObservation):
            text = obs.content
            # replace base64 images with a placeholder
            splitted = text.split('\n')
            for i, line in enumerate(splitted):
                if '![image](data:image/png;base64,' in line:
                    splitted[i] = (
                        '![image](data:image/png;base64, ...) already displayed to user'
                    )
            text = '\n'.join(splitted)
            text = truncate_content(text, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, FileEditObservation):
            text = truncate_content(str(obs), max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, FileReadObservation):
            message = Message(
                role='user', content=[TextContent(text=obs.content)]
            )  # Content is already truncated by openhands-aci
        elif isinstance(obs, BrowserOutputObservation):
            text = obs.get_agent_obs_text()
            if (
                obs.trigger_by_action == ActionType.BROWSE_INTERACTIVE
                and obs.set_of_marks is not None
                and len(obs.set_of_marks) > 0
                and enable_som_visual_browsing
                and vision_is_active
            ):
                text += 'Image: Current webpage screenshot (Note that only visible portion of webpage is present in the screenshot. You may need to scroll to view the remaining portion of the web-page.)\n'
                message = Message(
                    role='user',
                    content=[
                        TextContent(text=text),
                        ImageContent(image_urls=[obs.set_of_marks]),
                    ],
                )
            else:
                message = Message(
                    role='user',
                    content=[TextContent(text=text)],
                )
        elif isinstance(obs, AgentDelegateObservation):
            text = truncate_content(
                obs.outputs['content'] if 'content' in obs.outputs else '',
                max_message_chars,
            )
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, AgentThinkObservation):
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, ErrorObservation):
            text = truncate_content(obs.content, max_message_chars)
            text += '\n[Error occurred in processing last action]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, UserRejectObservation):
            text = 'OBSERVATION:\n' + truncate_content(obs.content, max_message_chars)
            text += '\n[Last action has been rejected by the user]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, AgentCondensationObservation):
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif (
            isinstance(obs, RecallObservation)
            and self.agent_config.enable_prompt_extensions
        ):
            if obs.recall_type == RecallType.WORKSPACE_CONTEXT:
                # everything is optional, check if they are present
                if obs.repo_name or obs.repo_directory:
                    repo_info = RepositoryInfo(
                        repo_name=obs.repo_name or '',
                        repo_directory=obs.repo_directory or '',
                    )
                else:
                    repo_info = None

                if obs.runtime_hosts or obs.additional_agent_instructions:
                    runtime_info = RuntimeInfo(
                        available_hosts=obs.runtime_hosts,
                        additional_agent_instructions=obs.additional_agent_instructions,
                    )
                else:
                    runtime_info = None

                repo_instructions = (
                    obs.repo_instructions if obs.repo_instructions else ''
                )

                # Have some meaningful content before calling the template
                has_repo_info = repo_info is not None and (
                    repo_info.repo_name or repo_info.repo_directory
                )
                has_runtime_info = runtime_info is not None and (
                    runtime_info.available_hosts
                    or runtime_info.additional_agent_instructions
                )
                has_repo_instructions = bool(repo_instructions.strip())

                # Filter and process microagent knowledge
                filtered_agents = []
                if obs.microagent_knowledge:
                    # Exclude disabled microagents
                    filtered_agents = [
                        agent
                        for agent in obs.microagent_knowledge
                        if agent.name not in self.agent_config.disabled_microagents
                    ]

                has_microagent_knowledge = bool(filtered_agents)

                # Generate appropriate content based on what is present
                message_content = []

                # Build the workspace context information
                if has_repo_info or has_runtime_info or has_repo_instructions:
                    formatted_workspace_text = (
                        self.prompt_manager.build_workspace_context(
                            repository_info=repo_info,
                            runtime_info=runtime_info,
                            repo_instructions=repo_instructions,
                        )
                    )
                    message_content.append(TextContent(text=formatted_workspace_text))

                # Add microagent knowledge if present
                if has_microagent_knowledge:
                    formatted_microagent_text = (
                        self.prompt_manager.build_microagent_info(
                            triggered_agents=filtered_agents,
                        )
                    )
                    message_content.append(TextContent(text=formatted_microagent_text))

                # Return the combined message if we have any content
                if message_content:
                    message = Message(role='user', content=message_content)
                else:
                    return []
            elif obs.recall_type == RecallType.KNOWLEDGE:
                # Use prompt manager to build the microagent info
                # First, filter out agents that appear in earlier RecallObservations
                filtered_agents = self._filter_agents_in_microagent_obs(
                    obs, current_index, events or []
                )

                # Create and return a message if there is microagent knowledge to include
                if filtered_agents:
                    # Exclude disabled microagents
                    filtered_agents = [
                        agent
                        for agent in filtered_agents
                        if agent.name not in self.agent_config.disabled_microagents
                    ]

                    # Only proceed if we still have agents after filtering out disabled ones
                    if filtered_agents:
                        formatted_text = self.prompt_manager.build_microagent_info(
                            triggered_agents=filtered_agents,
                        )

                        return [
                            Message(
                                role='user', content=[TextContent(text=formatted_text)]
                            )
                        ]

                # Return empty list if no microagents to include or all were disabled
                return []
        elif (
            isinstance(obs, RecallObservation)
            and not self.agent_config.enable_prompt_extensions
        ):
            # If prompt extensions are disabled, we don't add any additional info
            # TODO: test this
            return []
        else:
            # If an observation message is not returned, it will cause an error
            # when the LLM tries to return the next message
            raise ValueError(f'Unknown observation type: {type(obs)}')

        # Update the message as tool response properly
        if (tool_call_metadata := getattr(obs, 'tool_call_metadata', None)) is not None:
            tool_call_id_to_message[tool_call_metadata.tool_call_id] = Message(
                role='tool',
                content=message.content,
                tool_call_id=tool_call_metadata.tool_call_id,
                name=tool_call_metadata.function_name,
            )
            # No need to return the observation message
            # because it will be added by get_action_message when all the corresponding
            # tool calls in the SAME request are processed
            return []

        return [message]

    def apply_prompt_caching(self, messages: list[Message]) -> None:
        """Applies caching breakpoints to the messages.

        For new Anthropic API, we only need to mark the last user or tool message as cacheable.
        """
        # NOTE: this is only needed for anthropic
        for message in reversed(messages):
            if message.role in ('user', 'tool'):
                message.content[
                    -1
                ].cache_prompt = True  # Last item inside the message content
                break

    def _filter_agents_in_microagent_obs(
        self, obs: RecallObservation, current_index: int, events: list[Event]
    ) -> list[MicroagentKnowledge]:
        """Filter out agents that appear in earlier RecallObservations.

        Args:
            obs: The current RecallObservation to filter
            current_index: The index of the current event in the events list
            events: The list of all events

        Returns:
            list[MicroagentKnowledge]: The filtered list of microagent knowledge
        """
        if obs.recall_type != RecallType.KNOWLEDGE:
            return obs.microagent_knowledge

        # For each agent in the current microagent observation, check if it appears in any earlier microagent observation
        filtered_agents = []
        for agent in obs.microagent_knowledge:
            # Keep this agent if it doesn't appear in any earlier observation
            # that is, if this is the first microagent observation with this microagent
            if not self._has_agent_in_earlier_events(agent.name, current_index, events):
                filtered_agents.append(agent)

        return filtered_agents

    def _has_agent_in_earlier_events(
        self, agent_name: str, current_index: int, events: list[Event]
    ) -> bool:
        """Check if an agent appears in any earlier RecallObservation in the event list.

        Args:
            agent_name: The name of the agent to look for
            current_index: The index of the current event in the events list
            events: The list of all events

        Returns:
            bool: True if the agent appears in an earlier RecallObservation, False otherwise
        """
        for event in events[:current_index]:
            # Note that this check includes the WORKSPACE_CONTEXT
            if isinstance(event, RecallObservation):
                if any(
                    agent.name == agent_name for agent in event.microagent_knowledge
                ):
                    return True
        return False
