import warnings

from opendevin.core.config import LLMConfig

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from opendevin.condenser.condenser import CondenserMixin
from opendevin.controller.state.state import State
from opendevin.core.exceptions import (
    ContextWindowLimitExceededError,
    TokenLimitExceededError,
)
from opendevin.core.metrics import Metrics
from opendevin.llm.messages import Message

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

    # TODO Replace get_response with completion
    def get_response(self, messages: list[Message], state: State):
        try:
            if self.is_over_token_limit(messages):
                raise TokenLimitExceededError()
            response = self.completion(
                messages=self.get_text_messages(messages),
                stop=[
                    '</execute_ipython>',
                    '</execute_bash>',
                    '</execute_browse>',
                ],
                temperature=0.0,
            )
            return response
        except TokenLimitExceededError:
            # Handle the specific exception
            print('An error occurred: ')
            # If we got a context alert, try trimming the messages length, then try again
            if self.is_over_token_limit(messages):
                # A separate call to run a summarizer
                self.condense(messages=messages, state=state)
                # Try step again
            else:
                print('step() failed with an unrecognized exception:')
                raise ContextWindowLimitExceededError()
        return None
