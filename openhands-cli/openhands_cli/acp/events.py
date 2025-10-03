"""Event handling for ACP server."""

import logging
from typing import TYPE_CHECKING

from acp import SessionNotification
from acp.schema import (
    ContentBlock1,
    ContentBlock2,
    SessionUpdate2,
    SessionUpdate4,
    SessionUpdate5,
    ToolCallContent1,
    ToolCallLocation,
)

from openhands.agent_server.pub_sub import Subscriber
from openhands.sdk import ImageContent, TextContent
from openhands.sdk.event.base import LLMConvertibleEvent
from openhands.sdk.event.llm_convertible.action import ActionEvent
from openhands.sdk.event.llm_convertible.observation import (
    AgentErrorEvent,
    ObservationEvent,
    UserRejectObservation,
)

from .utils import get_tool_kind


if TYPE_CHECKING:
    from acp import AgentSideConnection

logger = logging.getLogger(__name__)


def _extract_locations(event: ActionEvent) -> list[ToolCallLocation] | None:
    """Extract file locations from an action event if available.

    Returns a list of ToolCallLocation objects if the action contains location
    information (e.g., file paths, directories), otherwise returns None.

    Supports:
    - str_replace_editor: path, view_range, insert_line
    - repomix_pack_codebase: directory
    - Other tools with 'path' or 'directory' attributes
    """
    locations = []

    # Check if action has a 'path' field (e.g., str_replace_editor)
    if hasattr(event.action, "path"):
        path = getattr(event.action, "path", None)
        if path:
            location = ToolCallLocation(path=path)

            # Check for line number information
            if hasattr(event.action, "view_range"):
                view_range = getattr(event.action, "view_range", None)
                if view_range and isinstance(view_range, list) and len(view_range) > 0:
                    location.line = view_range[0]
            elif hasattr(event.action, "insert_line"):
                insert_line = getattr(event.action, "insert_line", None)
                if insert_line is not None:
                    location.line = insert_line

            locations.append(location)

    # Check if action has a 'directory' field (e.g., repomix_pack_codebase)
    elif hasattr(event.action, "directory"):
        directory = getattr(event.action, "directory", None)
        if directory:
            locations.append(ToolCallLocation(path=directory))

    return locations if locations else None


def _rich_text_to_plain(text) -> str:
    """Convert Rich Text object to plain string.

    Args:
        text: Rich Text object or string

    Returns:
        Plain text string
    """
    if hasattr(text, "plain"):
        return text.plain
    return str(text)


class EventSubscriber(Subscriber):
    """Subscriber for handling OpenHands events and converting them to ACP
    notifications."""

    def __init__(self, session_id: str, conn: "AgentSideConnection"):
        """Initialize the event subscriber.

        Args:
            session_id: The ACP session ID
            conn: The ACP connection for sending notifications
        """
        self.session_id = session_id
        self.conn = conn

    async def __call__(self, event):
        """Handle incoming events and convert them to ACP notifications."""
        # Handle different event types
        if isinstance(event, ActionEvent):
            await self._handle_action_event(event)
        elif isinstance(
            event, (ObservationEvent, UserRejectObservation, AgentErrorEvent)
        ):
            await self._handle_observation_event(event)
        elif isinstance(event, LLMConvertibleEvent):
            await self._handle_llm_convertible_event(event)

    async def _handle_action_event(self, event: ActionEvent):
        """Handle ActionEvent: send thought as agent_message_chunk, then tool_call."""
        try:
            # First, send thoughts/reasoning as agent_message_chunk if available
            thought_text = " ".join([t.text for t in event.thought])

            # Send reasoning content first if available
            if event.reasoning_content and event.reasoning_content.strip():
                await self.conn.sessionUpdate(
                    SessionNotification(
                        sessionId=self.session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text",
                                text=event.reasoning_content,
                            ),
                        ),
                    )
                )

            # Then send thought as agent_message_chunk
            if thought_text.strip():
                await self.conn.sessionUpdate(
                    SessionNotification(
                        sessionId=self.session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text",
                                text=thought_text,
                            ),
                        ),
                    )
                )

            # Now send the tool_call with action.visualize content
            tool_kind = get_tool_kind(event.tool_name)

            # Use action.title for a brief summary
            title = event.action.title

            # Use action.visualize for rich content
            action_viz = _rich_text_to_plain(event.action.visualize)

            # Extract locations if available
            locations = _extract_locations(event)

            await self.conn.sessionUpdate(
                SessionNotification(
                    sessionId=self.session_id,
                    update=SessionUpdate4(
                        sessionUpdate="tool_call",
                        toolCallId=event.tool_call_id,
                        title=title,
                        kind=tool_kind,
                        status="pending",
                        content=[
                            ToolCallContent1(
                                type="content",
                                content=ContentBlock1(
                                    type="text",
                                    text=action_viz,
                                ),
                            )
                        ]
                        if action_viz.strip()
                        else None,
                        locations=locations,
                        rawInput=event.tool_call.function.arguments
                        if hasattr(event.tool_call.function, "arguments")
                        else None,
                    ),
                )
            )
        except Exception as e:
            logger.debug(f"Error processing ActionEvent: {e}")

    async def _handle_observation_event(
        self, event: ObservationEvent | UserRejectObservation | AgentErrorEvent
    ):
        """Handle observation events by sending tool_call_update notification."""
        try:
            # Use visualize property for rich content
            viz_text = _rich_text_to_plain(event.visualize)

            # Determine status
            if isinstance(event, ObservationEvent):
                status = "completed"
            else:  # UserRejectObservation or AgentErrorEvent
                status = "failed"

            # Extract raw output for structured data
            raw_output = None
            if isinstance(event, ObservationEvent):
                # Extract content from observation for raw output
                content_parts = []
                for item in event.observation.to_llm_content:
                    if isinstance(item, TextContent):
                        content_parts.append(item.text)
                    elif hasattr(item, "text") and not isinstance(item, ImageContent):
                        content_parts.append(getattr(item, "text"))
                    else:
                        content_parts.append(str(item))
                content_text = "".join(content_parts)
                if content_text.strip():
                    raw_output = {"result": content_text}
            elif isinstance(event, UserRejectObservation):
                raw_output = {"rejection_reason": event.rejection_reason}
            else:  # AgentErrorEvent
                raw_output = {"error": event.error}

            await self.conn.sessionUpdate(
                SessionNotification(
                    sessionId=self.session_id,
                    update=SessionUpdate5(
                        sessionUpdate="tool_call_update",
                        toolCallId=event.tool_call_id,
                        status=status,
                        content=[
                            ToolCallContent1(
                                type="content",
                                content=ContentBlock1(
                                    type="text",
                                    text=viz_text,
                                ),
                            )
                        ]
                        if viz_text.strip()
                        else None,
                        rawOutput=raw_output,
                    ),
                )
            )
        except Exception as e:
            logger.debug(f"Error processing observation event: {e}")

    async def _handle_llm_convertible_event(self, event: LLMConvertibleEvent):
        """Handle other LLMConvertibleEvent events."""
        try:
            llm_message = event.to_llm_message()

            # Send the event as a session update
            if llm_message.role == "assistant":
                # Send all content items from the LLM message
                for content_item in llm_message.content:
                    if isinstance(content_item, TextContent):
                        if content_item.text.strip():
                            # Send text content
                            await self.conn.sessionUpdate(
                                SessionNotification(
                                    sessionId=self.session_id,
                                    update=SessionUpdate2(
                                        sessionUpdate="agent_message_chunk",
                                        content=ContentBlock1(
                                            type="text",
                                            text=content_item.text,
                                        ),
                                    ),
                                )
                            )
                    elif isinstance(content_item, ImageContent):
                        # Send each image URL as separate content
                        for image_url in content_item.image_urls:
                            # Determine if it's a URI or base64 data
                            is_uri = image_url.startswith(("http://", "https://"))
                            await self.conn.sessionUpdate(
                                SessionNotification(
                                    sessionId=self.session_id,
                                    update=SessionUpdate2(
                                        sessionUpdate="agent_message_chunk",
                                        content=ContentBlock2(
                                            type="image",
                                            data=image_url,
                                            mimeType="image/png",
                                            uri=image_url if is_uri else None,
                                        ),
                                    ),
                                )
                            )
                    elif isinstance(content_item, str):
                        if content_item.strip():
                            # Send string content as text
                            await self.conn.sessionUpdate(
                                SessionNotification(
                                    sessionId=self.session_id,
                                    update=SessionUpdate2(
                                        sessionUpdate="agent_message_chunk",
                                        content=ContentBlock1(
                                            type="text",
                                            text=content_item,
                                        ),
                                    ),
                                )
                            )
        except Exception as e:
            logger.debug(f"Error processing LLMConvertibleEvent: {e}")
