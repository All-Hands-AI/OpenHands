from opendevin.controller.state.state import State
from opendevin.core.exceptions import (
    SummarizeError,
)
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    AgentSummarizeAction,
)
from opendevin.llm.messages import Message

from .prompts import (
    MESSAGE_SUMMARY_WARNING_FRAC,
    SUMMARY_PROMPT_SYSTEM,
    parse_summary_response,
)


class CondenserMixin:
    """Condenses a group of condensable messages as done by MemGPT."""

    def condense(
        self,
        messages: list[Message],
        state: State,
    ):
        # Start past the system message, and example messages.,
        # and collect messages for summarization until we reach the desired truncation token fraction (eg 50%)
        # Do not allow truncation  for in-context examples of function calling
        token_counts = [
            self.get_token_count([message])  # type: ignore
            for message in messages
            if message.condensable
        ]
        message_buffer_token_count = sum(token_counts)  # no system and example message

        desired_token_count_to_summarize = int(
            message_buffer_token_count * self.config.message_summary_trunc_tokens_frac  # type: ignore
        )

        candidate_messages_to_summarize = []
        tokens_so_far = 0
        for message in messages:
            if message.condensable:
                candidate_messages_to_summarize.append(message)
                tokens_so_far += self.get_token_count([message])  # type: ignore
            if tokens_so_far > desired_token_count_to_summarize:
                last_summarized_event_id = message.event_id
                break

        # TODO: Add functionality for preserving last N messages
        # MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST = 3
        # if preserve_last_N_messages:
        #     candidate_messages_to_summarize = candidate_messages_to_summarize[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]
        #     token_counts = token_counts[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]

        logger.debug(
            f'message_summary_trunc_tokens_frac={self.config.message_summary_trunc_tokens_frac}'  # type: ignore
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
        context_window = self.config.max_input_tokens  # type: ignore
        summary_prompt = SUMMARY_PROMPT_SYSTEM
        summary_input = self._format_summary_history(
            self.get_text_messages(message_sequence_to_summarize)  # type: ignore
        )
        summary_input_tkns = self.get_token_count(summary_input)  # type: ignore
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

        response = self.completion(  # type: ignore
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
