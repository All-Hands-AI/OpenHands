import warnings

from opendevin.core.config import LLMConfig

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from opendevin.condenser.condenser import CondenserMixin
from opendevin.core.exceptions import (
    ContextWindowLimitExceededError,
    TokenLimitExceededError,
)
from opendevin.core.logger import llm_prompt_logger, llm_response_logger
from opendevin.core.metrics import Metrics

from .basellm import BaseLLM

__all__ = ['LLM']

message_separator = '\n\n----------\n\n'


class LLM(BaseLLM, CondenserMixin):
    """The LLM class represents a Language Model instance.

    Attributes:
        config: an LLMConfig object specifying the configuration of the LLM.
    """

    def __init__(
        self,
        config: LLMConfig,
        metrics: Metrics | None = None,
    ):
        super().__init__(config, metrics)

        def wrapper(*args, **kwargs):
            """Wrapper for the litellm completion function. Logs the input and output of the completion function."""
            # some callers might just send the messages directly
            if 'messages' in kwargs:
                messages = kwargs['messages']
            else:
                messages = args[1]

            try:
                if self.is_over_token_limit(messages):
                    raise TokenLimitExceededError()
            except TokenLimitExceededError:
                print('An error occurred: ')
                # If we got a context alert, try trimming the messages length, then try again
                # if kwargs['condense'] and self.is_over_token_limit(messages):
                if self.is_over_token_limit(messages):
                    # A separate call to run a summarizer
                    summary_action = self.condense(messages=messages)
                    return summary_action
                else:
                    print('step() failed with an unrecognized exception:')
                    raise ContextWindowLimitExceededError()

            text_messages = [message.model_dump() for message in messages]

            # log the prompt
            debug_message = ''
            for message in text_messages:
                content = message['content']

                if isinstance(content, list):
                    for element in content:
                        if isinstance(element, dict):
                            if 'text' in element:
                                content_str = element['text'].strip()
                            elif (
                                'image_url' in element and 'url' in element['image_url']
                            ):
                                content_str = element['image_url']['url']
                            else:
                                content_str = str(element)
                        else:
                            content_str = str(element)

                        debug_message += message_separator + content_str
                else:
                    content_str = str(content)
                    debug_message += message_separator + content_str

            llm_prompt_logger.debug(debug_message)

            kwargs = {
                'messages': text_messages,
                'stop': kwargs['stop'],
                'temperature': kwargs['temperature'],
            }

            # skip if messages is empty (thus debug_message is empty)
            if debug_message:
                resp = self.completion_unwrapped(*args, **kwargs)
            else:
                resp = {'choices': [{'message': {'content': ''}}]}

            # log the response
            message_back = resp['choices'][0]['message']['content']
            llm_response_logger.debug(message_back)

            # post-process to log costs
            self._post_completion(resp)

            return resp

        self._completion = wrapper  # type: ignore

    @property
    def completion(self):
        return self._completion
