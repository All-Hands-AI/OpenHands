from typing import Any

from openhands.core.logger import llm_prompt_logger, llm_response_logger
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message

MESSAGE_SEPARATOR = '\n\n----------\n\n'


class DebugMixin:
    def log_prompt(
        self, messages: list[Message | dict[str, Any]] | Message | dict[str, Any]
    ):
        if not messages:
            logger.debug('No completion messages!')
            return

        messages = messages if isinstance(messages, list) else [messages]
        debug_message = MESSAGE_SEPARATOR.join(
            self._format_content_as_string(msg)
            for msg in messages
            if self._get_message_content(msg)
        )

        if debug_message:
            llm_prompt_logger.debug(debug_message)
        else:
            logger.debug('No completion messages!')

    def log_response(self, message_back: str):
        if message_back:
            llm_response_logger.debug(message_back)

    def _get_message_content(self, message: Message | dict[str, Any]):
        if isinstance(message, Message):
            return message.content
        return message.get('content', None)

    def _format_content_as_string(self, message: Message | dict[str, Any]) -> str:
        content = self._get_message_content(message)
        if isinstance(content, list):
            return '\n'.join(
                self._format_content_element_as_string(element) for element in content
            )
        return str(content)

    def _format_content_element_as_string(self, element: dict[str, Any]) -> str:
        if isinstance(element, dict):
            if 'text' in element:
                return element['text']
            if (
                self.vision_is_active()
                and 'image_url' in element
                and 'url' in element['image_url']
            ):
                return element['image_url']['url']
        return str(element)

    # This method should be implemented in the class that uses DebugMixin
    def vision_is_active(self):
        raise NotImplementedError
