from dataclasses import dataclass
from typing import Optional

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class MessageAction(Action):
    content: str
    image_urls: list[str] | None = None
    wait_for_response: bool = False
    action: str = ActionType.MESSAGE
    security_risk: ActionSecurityRisk | None = None
    mode: str | None = None
    enable_think: Optional[bool] = True  # type: ignore

    @property
    def message(self) -> str:
        return self.content

    @property
    def images_urls(self) -> list[str] | None:
        # Deprecated alias for backward compatibility
        return self.image_urls

    @images_urls.setter
    def images_urls(self, value: list[str] | None) -> None:
        self.image_urls = value

    def __str__(self) -> str:
        ret = f'**MessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        if self.image_urls:
            for url in self.image_urls:
                ret += f'\nIMAGE_URL: {url}'
        return ret


@dataclass
class StreamingMessageAction(Action):
    """
    A special message action only for streaming output to the UI.
    This action is ignored by the agent controller and doesn't affect state management.

    Usage:
        # For streaming LLM output to UI
        action = StreamingMessageAction(content="Hello, I'm thinking...")
        event_stream.add_event(action, EventSource.AGENT)

        # The action will be sent to UI but won't trigger agent state changes
    """

    content: str
    action: str = ActionType.STREAMING_MESSAGE
    wait_for_response: bool = False
    streaming: bool = True
    enable_process_llm: Optional[bool] = True

    @property
    def message(self) -> str:
        return self.content

    def __str__(self) -> str:
        ret = f'**StreamingMessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        return ret
