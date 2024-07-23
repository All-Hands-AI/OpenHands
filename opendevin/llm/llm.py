import copy
import warnings
from functools import partial

from opendevin.core.config import LLMConfig

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
from litellm import completion as litellm_completion
from litellm import completion_cost as litellm_completion_cost
from litellm.exceptions import (
    APIConnectionError,
    ContentPolicyViolationError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
)
from litellm.types.utils import CostPerToken
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from opendevin.controller.state.state import State
from opendevin.core.exceptions import (
    ContextWindowLimitExceededError,
    SummarizeError,
    TokenLimitExceededError,
)
from opendevin.core.logger import llm_prompt_logger, llm_response_logger
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.metrics import Metrics
from opendevin.events.action import (
    AgentSummarizeAction,
)
from opendevin.llm.messages import Message

from .prompts import (
    MESSAGE_SUMMARY_WARNING_FRAC,
    SUMMARY_PROMPT_SYSTEM,
    parse_summary_response,
)

__all__ = ['LLM']

message_separator = '\n\n----------\n\n'


class LLM:
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

        self.config = copy.deepcopy(config)
        self.metrics = metrics if metrics is not None else Metrics()
        self.cost_metric_supported = True
        # self.memory_condenser = MemoryCondenser()

        # litellm actually uses base Exception here for unknown model
        self.model_info = None
        try:
            if not config.model.startswith('openrouter'):
                self.model_info = litellm.get_model_info(config.model.split(':')[0])
            else:
                self.model_info = litellm.get_model_info(config.model)
        # noinspection PyBroadException
        except Exception:
            logger.warning(f'Could not get model info for {config.model}')

        # Set the max tokens in an LM-specific way if not set
        if config.max_input_tokens is None:
            if (
                self.model_info is not None
                and 'max_input_tokens' in self.model_info
                and isinstance(self.model_info['max_input_tokens'], int)
            ):
                self.config.max_input_tokens = self.model_info['max_input_tokens']
            else:
                # Max input tokens for gpt3.5, so this is a safe fallback for any potentially viable model
                self.config.max_input_tokens = 4096
        if config.max_output_tokens is None:
            if (
                self.model_info is not None
                and 'max_output_tokens' in self.model_info
                and isinstance(self.model_info['max_output_tokens'], int)
            ):
                self.config.max_output_tokens = self.model_info['max_output_tokens']
            else:
                # Max output tokens for gpt3.5, so this is a safe fallback for any potentially viable model
                self.config.max_output_tokens = 1024

        self._completion = partial(
            litellm_completion,
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            max_tokens=self.config.max_output_tokens,
            timeout=self.config.timeout,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
        )

        completion_unwrapped = self._completion

        def attempt_on_error(retry_state):
            logger.error(
                f'{retry_state.outcome.exception()}. Attempt #{retry_state.attempt_number} | You can customize these settings in the configuration.',
                exc_info=False,
            )
            return None

        @retry(
            reraise=True,
            stop=stop_after_attempt(config.num_retries),
            wait=wait_random_exponential(
                multiplier=config.retry_multiplier,
                min=config.retry_min_wait,
                max=config.retry_max_wait,
            ),
            retry=retry_if_exception_type(
                (
                    RateLimitError,
                    APIConnectionError,
                    ServiceUnavailableError,
                    InternalServerError,
                    ContentPolicyViolationError,
                )
            ),
            after=attempt_on_error,
        )
        def wrapper(*args, **kwargs):
            """Wrapper for the litellm completion function. Logs the input and output of the completion function."""
            # some callers might just send the messages directly
            if 'messages' in kwargs:
                messages = kwargs['messages']
            else:
                messages = args[1]

            # log the prompt
            debug_message = ''
            for message in messages:
                debug_message += message_separator + message['content']
            llm_prompt_logger.debug(debug_message)

            # call the completion function
            resp = completion_unwrapped(*args, **kwargs)

            # log the response
            message_back = resp['choices'][0]['message']['content']
            llm_response_logger.debug(message_back)

            # post-process to log costs
            self._post_completion(resp)
            return resp

        self._completion = wrapper  # type: ignore

    @property
    def completion(self):
        """Decorator for the litellm completion function.

        Check the complete documentation at https://litellm.vercel.app/docs/completion
        """
        return self._completion

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

    def _post_completion(self, response: str) -> None:
        """Post-process the completion response."""
        try:
            cur_cost = self.completion_cost(response)
        except Exception:
            cur_cost = 0
        if self.cost_metric_supported:
            logger.info(
                'Cost: %.2f USD | Accumulated Cost: %.2f USD',
                cur_cost,
                self.metrics.accumulated_cost,
            )

    def get_token_count(self, messages):
        """Get the number of tokens in a list of messages.

        Args:
            messages (list): A list of messages.

        Returns:
            int: The number of tokens.
        """
        if isinstance(messages, list):
            text_messages = self.get_text_messages(messages)
            return litellm.token_counter(
                model=self.config.model, messages=text_messages
            )
        elif isinstance(messages, str):
            return litellm.token_counter(model=self.config.model, text=messages)

    def is_local(self):
        """Determines if the system is using a locally running LLM.

        Returns:
            boolean: True if executing a local model.
        """
        if self.config.base_url is not None:
            for substring in ['localhost', '127.0.0.1' '0.0.0.0']:
                if substring in self.config.base_url:
                    return True
        elif self.config.model is not None:
            if self.config.model.startswith('ollama'):
                return True
        return False

    def completion_cost(self, response):
        """Calculate the cost of a completion response based on the model.  Local models are treated as free.
        Add the current cost into total cost in metrics.

        Args:
            response: A response from a model invocation.

        Returns:
            number: The cost of the response.
        """
        if not self.cost_metric_supported:
            return 0.0

        extra_kwargs = {}
        if (
            self.config.input_cost_per_token is not None
            and self.config.output_cost_per_token is not None
        ):
            cost_per_token = CostPerToken(
                input_cost_per_token=self.config.input_cost_per_token,
                output_cost_per_token=self.config.output_cost_per_token,
            )
            logger.info(f'Using custom cost per token: {cost_per_token}')
            extra_kwargs['custom_cost_per_token'] = cost_per_token

        if not self.is_local():
            try:
                cost = litellm_completion_cost(
                    completion_response=response, **extra_kwargs
                )
                self.metrics.add_cost(cost)
                return cost
            except Exception:
                self.cost_metric_supported = False
                logger.warning('Cost calculation not supported for this model.')
        return 0.0

    def __str__(self):
        if self.config.api_version:
            return f'LLM(model={self.config.model}, api_version={self.config.api_version}, base_url={self.config.base_url})'
        elif self.config.base_url:
            return f'LLM(model={self.config.model}, base_url={self.config.base_url})'
        return f'LLM(model={self.config.model})'

    def __repr__(self):
        return str(self)

    def is_over_token_limit(self, messages: list[Message]) -> bool:
        """
        Estimates the token count of the given events using litellm tokenizer and returns True if over the max_input_tokens value.

        Parameters:
        - messages: List of messages to estimate the token count for.

        Returns:
        - Estimated token count.
        """
        # max_input_tokens will always be set in init to some sensible default
        # 0 in config.llm disables the check
        MAX_TOKEN_COUNT_PADDING = 512
        if not self.config.max_input_tokens:
            return False
        token_count = self.get_token_count(messages=messages) + MAX_TOKEN_COUNT_PADDING
        return token_count >= self.config.max_input_tokens

    def get_text_messages(self, messages: list[Message]) -> list[dict]:
        text_messages = []
        for message in messages:
            text_messages.append(message.message)
        return text_messages

    def condense(
        self,
        messages: list[Message],
        state: State,
    ):
        # Start past the system message, and example messages.,
        # and collect messages for summarization until we reach the desired truncation token fraction (eg 50%)
        # Do not allow truncation  for in-context examples of function calling
        token_counts = [
            self.get_token_count([message])
            for message in messages
            if message.condensable
        ]
        message_buffer_token_count = sum(token_counts)  # no system and example message

        desired_token_count_to_summarize = int(
            message_buffer_token_count * self.config.message_summary_trunc_tokens_frac
        )

        candidate_messages_to_summarize = []
        tokens_so_far = 0
        for message in messages:
            if message.condensable:
                candidate_messages_to_summarize.append(message)
                tokens_so_far += self.get_token_count([message])
            if tokens_so_far > desired_token_count_to_summarize:
                last_summarized_event_id = message.event_id
                break

        # TODO: Add functionality for preserving last N messages
        # MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST = 3
        # if preserve_last_N_messages:
        #     candidate_messages_to_summarize = candidate_messages_to_summarize[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]
        #     token_counts = token_counts[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]

        logger.debug(
            f'message_summary_trunc_tokens_frac={self.config.message_summary_trunc_tokens_frac}'
        )
        # logger.debug(f'MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST={MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST}')
        logger.debug(f'token_counts={token_counts}')
        logger.debug(f'message_buffer_token_count={message_buffer_token_count}')
        logger.debug(
            f'desired_token_count_to_summarize={desired_token_count_to_summarize}'
        )
        logger.debug(
            f'len(candidate_messages_to_summarize)={len(candidate_messages_to_summarize)}'
        )

        if len(candidate_messages_to_summarize) == 0:
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(messages)}]"
            )

        # TODO: Try to make an assistant message come after the cutoff

        message_sequence_to_summarize = candidate_messages_to_summarize

        if len(message_sequence_to_summarize) <= 1:
            # This prevents a potential infinite loop of summarizing the same message over and over
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(message_sequence_to_summarize)} <= 1]"
            )
        else:
            print(
                f'Attempting to summarize with last summarized event id = {last_summarized_event_id}'
            )

        summary_action: AgentSummarizeAction = self.summarize_messages(
            message_sequence_to_summarize=message_sequence_to_summarize
        )
        summary_action.last_summarized_event_id = (
            last_summarized_event_id if last_summarized_event_id else -1
        )
        print(f'Got summary: {summary_action}')
        state.history.add_summary(summary_action)
        print('Added summary to history')

    def _format_summary_history(self, message_history: list[dict]) -> str:
        # TODO use existing prompt formatters for this (eg ChatML)
        return '\n'.join([f'{m["role"]}: {m["content"]}' for m in message_history])

    def summarize_messages(self, message_sequence_to_summarize: list[Message]):
        """Summarize a message sequence using LLM"""
        context_window = self.config.max_input_tokens
        summary_prompt = SUMMARY_PROMPT_SYSTEM
        summary_input = self._format_summary_history(
            self.get_text_messages(message_sequence_to_summarize)
        )
        summary_input_tkns = self.get_token_count(summary_input)
        if context_window is None:
            raise ValueError('context_window should not be None')
        if summary_input_tkns > MESSAGE_SUMMARY_WARNING_FRAC * context_window:
            trunc_ratio = (
                MESSAGE_SUMMARY_WARNING_FRAC * context_window / summary_input_tkns
            ) * 0.8  # For good measure...
            cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)
            summary_input = str(
                [
                    self.summarize_messages(
                        message_sequence_to_summarize=message_sequence_to_summarize[
                            :cutoff
                        ]
                    )
                ]
                + message_sequence_to_summarize[cutoff:]
            )

        message_sequence = []
        message_sequence.append({'role': 'system', 'content': summary_prompt})

        # TODO: Check if this feature is needed
        # if insert_acknowledgement_assistant_message:
        #     message_sequence.append(Message(user_id=dummy_user_id, agent_id=dummy_agent_id, role="assistant", text=MESSAGE_SUMMARY_REQUEST_ACK))

        message_sequence.append({'role': 'user', 'content': summary_input})

        response = self.completion(
            messages=message_sequence,
            stop=[
                '</execute_ipython>',
                '</execute_bash>',
                '</execute_browse>',
            ],
            temperature=0.0,
        )

        print(f'summarize_messages gpt reply: {response.choices[0]}')

        action_response = response['choices'][0]['message']['content']
        action = parse_summary_response(action_response)
        return action
