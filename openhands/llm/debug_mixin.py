from typing import Any

from openhands.core.logger import llm_prompt_logger, llm_response_logger
from openhands.core.logger import openhands_logger as logger

MESSAGE_SEPARATOR = '\n\n----------\n\n'


class DebugMixin:
    def log_prompt(self, messages: list[dict[str, Any]] | dict[str, Any]):
        if not messages:
            logger.debug('No completion messages!')
            return

        messages = messages if isinstance(messages, list) else [messages]
        debug_message = MESSAGE_SEPARATOR.join(
            self._format_message_content(msg)
            for msg in messages
            if msg['content'] is not None
        )

        if debug_message:
            llm_prompt_logger.debug(debug_message)
        else:
            logger.debug('No completion messages!')

    def log_response(self, message_back: str):
        if message_back:
            llm_response_logger.debug(message_back)

    def _format_message_content(self, message: dict[str, Any]):
        content = message['content']
        if isinstance(content, list):
            return '\n'.join(
                self._format_content_element(element) for element in content
            )
        return str(content)

    def _format_content_element(self, element: dict[str, Any]):
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
