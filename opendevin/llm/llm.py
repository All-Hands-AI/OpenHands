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
        """Initializes the LLM. If LLMConfig is passed, its values will be the fallback.

        Passing simple parameters always overrides config.

        Args:
            config: The LLM configuration
        """
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
                if kwargs['condense'] and self.is_over_token_limit(messages):
                    # A separate call to run a summarizer
                    summary_action = self.condense(messages=messages)
                    return summary_action
                else:
                    print('step() failed with an unrecognized exception:')
                    raise ContextWindowLimitExceededError()

            # log the prompt
            debug_message = ''
            for message in messages:
                debug_message += message_separator + message.message['content']
            llm_prompt_logger.debug(debug_message)

            # get the messages in form of list[str]
            text_messages = self.get_text_messages(messages)

            # call the completion function
            kwargs = {
                'messages': text_messages,
                'stop': kwargs['stop'],
                'temperature': kwargs['temperature'],
            }
            resp = self.completion_unwrapped(**kwargs)

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
