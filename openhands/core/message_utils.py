from litellm import ModelResponse

from openhands.core.logger import openhands_logger as logger
from openhands.core.message import ImageContent, Message, TextContent
from openhands.core.schema import ActionType
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentCondensationObservation,
    AgentDelegateObservation,
    BrowserOutputObservation,
    CmdOutputObservation,
    FileEditObservation,
    FileReadObservation,
    IPythonRunCellObservation,
    UserRejectObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.observation import Observation
from openhands.events.serialization.event import truncate_content


def events_to_messages(
    events: list[Event],
    max_message_chars: int | None = None,
    vision_is_active: bool = False,
    enable_som_visual_browsing: bool = False,
) -> list[Message]:
    """Converts a list of events into a list of messages that can be sent to the LLM.

    Ensures that tool call actions are processed correctly in function calling mode.

    Args:
        events: A list of events to convert. Each event can be an Action or Observation.
        max_message_chars: The maximum number of characters in the content of an event included in the prompt to the LLM.
            Larger observations are truncated.
        vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included.
        enable_som_visual_browsing: Whether to enable visual browsing for the SOM model.
    """
    messages = []

    pending_tool_call_action_messages: dict[str, Message] = {}
    tool_call_id_to_message: dict[str, Message] = {}

    for event in events:
        # create a regular message from an event
        if isinstance(event, Action):
            messages_to_add = get_action_message(
                action=event,
                pending_tool_call_action_messages=pending_tool_call_action_messages,
                vision_is_active=vision_is_active,
            )
        elif isinstance(event, Observation):
            messages_to_add = get_observation_message(
                obs=event,
                tool_call_id_to_message=tool_call_id_to_message,
                max_message_chars=max_message_chars,
                vision_is_active=vision_is_active,
                enable_som_visual_browsing=enable_som_visual_browsing,
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


def get_action_message(
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
        assistant_msg = llm_response.choices[0].message

        # Add the LLM message (assistant) that initiated the tool calls
        # (overwrites any previous message with the same response_id)
        logger.debug(
            f'Tool calls type: {type(assistant_msg.tool_calls)}, value: {assistant_msg.tool_calls}'
        )
        pending_tool_call_action_messages[llm_response.id] = Message(
            role=assistant_msg.role,
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
            assistant_msg = tool_metadata.model_response.choices[0].message
            content = assistant_msg.content or ''

            # save content if any, to thought
            if action.thought:
                if action.thought != content:
                    action.thought += '\n' + content
            else:
                action.thought = content

            # remove the tool call metadata
            action.tool_call_metadata = None
        return [
            Message(
                role=role,
                content=[TextContent(text=action.thought)],
            )
        ]
    elif isinstance(action, MessageAction):
        role = 'user' if action.source == 'user' else 'assistant'
        content = [TextContent(text=action.content or '')]
        if vision_is_active and action.image_urls:
            content.append(ImageContent(image_urls=action.image_urls))
        return [
            Message(
                role=role,
                content=content,
            )
        ]
    elif isinstance(action, CmdRunAction) and action.source == 'user':
        content = [TextContent(text=f'User executed the command:\n{action.command}')]
        return [
            Message(
                role='user',
                content=content,
            )
        ]
    return []


def get_observation_message(
    obs: Observation,
    tool_call_id_to_message: dict[str, Message],
    max_message_chars: int | None = None,
    vision_is_active: bool = False,
    enable_som_visual_browsing: bool = False,
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
    else:
        # If an observation message is not returned, it will cause an error
        # when the LLM tries to return the next message
        raise ValueError(f'Unknown observation type: {type(obs)}')

    # Update the message as tool response properly
    if (tool_call_metadata := obs.tool_call_metadata) is not None:
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


def apply_prompt_caching(messages: list[Message]) -> None:
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
