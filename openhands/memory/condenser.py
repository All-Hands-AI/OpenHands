from litellm.types.utils import ModelResponse

from openhands.core.exceptions import SummarizeError
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import AgentSummarizeAction
from openhands.llm.llm import LLM
from openhands.memory.utils import parse_summary_response
from openhands.utils.prompt import PromptManager

WORD_LIMIT = 200


class MemoryCondenser:
    def __init__(self, llm: LLM, prompt_manager: PromptManager):
        self.llm = llm
        self.prompt_manager = prompt_manager

        # just easier to read
        self.context_window = llm.config.max_input_tokens
        assert (
            self.context_window is not None and self.context_window > 2000
        ), 'context window must be a number over 2000'

    def condense(
        self,
        messages: list[Message],
    ) -> AgentSummarizeAction:
        """
        Condenses a list of messages using the LLM and returns a summary action.

        Args:
            messages (list[Message]): The list of messages to condense.

        Returns:
            AgentSummarizeAction: The summary action containing the condensed summary.
        """
        # don't condense if under the token limit
        total_token_count = self.llm.get_token_count(messages)
        if total_token_count < self.context_window:
            logger.debug(
                f'Not condensing messages because token count ({total_token_count}) is less than max input tokens ({self.context_window})'
            )
            return AgentSummarizeAction(end_id=-1)

        # the system message and example messages are not condensable
        # collect messages for summarization until we reach the desired truncation token fraction
        token_counts = [
            self.llm.get_token_count([message.model_dump()])
            for message in messages
            if message.condensable
        ]
        message_buffer_token_count = sum(token_counts)

        desired_token_count_to_summarize = int(
            message_buffer_token_count * self.llm.config.message_summary_warning_level
        )

        # log status
        logger.debug(
            f'{len(messages)} messages in buffer: {message_buffer_token_count} tokens >> '
            f'{desired_token_count_to_summarize} tokens'
        )

        candidate_messages_to_summarize: list[Message] = []
        tokens_so_far = 0
        last_summarized_event_id = -1

        # collect messages until we reach the desired size
        for message in messages:
            if message.condensable:
                logger.debug(
                    f'condensable message: {message.event_id}: {str(message.content)[:30]}'
                )
                tokens_so_far += self.llm.get_token_count([message.model_dump()])
            if tokens_so_far <= desired_token_count_to_summarize:
                candidate_messages_to_summarize.append(message)
                last_summarized_event_id = message.event_id
            else:
                break

        logger.debug(
            f'len(candidate_messages_to_summarize)={len(candidate_messages_to_summarize)}'
        )

        if len(candidate_messages_to_summarize) <= 1:
            # Prevents potential infinite loop of summarizing the same message repeatedly
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(candidate_messages_to_summarize)} <= 1]"
            )
        else:
            logger.debug(
                f'Attempting to summarize with last summarized event id = {last_summarized_event_id}'
            )

        # perform the operation
        action_response = self._summarize_messages(
            message_sequence_to_summarize=candidate_messages_to_summarize
        )

        # we get an AgentSummarizeAction
        summary_action: AgentSummarizeAction = parse_summary_response(action_response)
        summary_action.end_id = last_summarized_event_id

        # Serialize and save messages along with the summary action for debugging
        self._save_messages_for_debugging(messages, summary_action)

        return summary_action

    def _format_summary_history(self, message_history: list[dict]) -> str:
        # TODO use existing prompt formatters for this (eg ChatML)
        return '\n'.join([f'{m["role"]}: {m["content"]}' for m in message_history])

    def _summarize_messages(self, message_sequence_to_summarize: list[Message]):
        """Summarize a message sequence using LLM"""

        assert self.context_window is not None, 'context window must be set'

        # we have a template to fill in with:
        # - message history

        # FIXME: Render the template with the message history
        token_count = self.llm.get_token_count(message_sequence_to_summarize)

        # check if the token count exceeds the allowed summary level
        if (
            token_count
            > self.llm.config.message_summary_warning_level * self.context_window
        ):
            trunc_ratio = (
                self.llm.config.message_summary_warning_level
                * self.context_window
                / token_count
            ) * 0.8  # For good measure...
            cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)

            # recursively summarize the first part to fit within the context window
            curr_summary: AgentSummarizeAction = parse_summary_response(
                self._summarize_messages(
                    message_sequence_to_summarize=message_sequence_to_summarize[:cutoff]
                )
            )

            # prepare for the next round
            curr_summary_message = (
                'Summary of all Action and Observations till now: \n'
                + curr_summary.summary
            )
            logger.debug(f'curr_summary_message: {curr_summary_message}')

            # the rest of the messages
            message_sequence_to_summarize = message_sequence_to_summarize[cutoff:]

            curr_summary_message = [TextContent(text=curr_summary_message)]
            message_sequence_to_summarize.insert(
                0, Message(role='user', content=curr_summary_message)
            )

        # build the message to send
        self.prompt_manager.conversation_history = self.llm.format_messages_for_llm(
            message_sequence_to_summarize
        )
        summarize_prompt = self.prompt_manager.summarize_message
        message = Message(role='system', content=[TextContent(text=summarize_prompt)])
        serialized_message = message.model_dump()

        response = self.llm.completion(
            messages=[serialized_message],
            temperature=0.2,
        )

        print(f'summarize_messages got response: {response}')
        assert isinstance(response, ModelResponse), 'response must be a ModelResponse'

        action_response = response.choices[0].message.content
        return action_response
