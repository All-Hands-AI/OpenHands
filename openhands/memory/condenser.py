from litellm.types.utils import ModelResponse

from openhands.core.exceptions import SummarizeError
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import AgentSummarizeAction
from openhands.llm.llm import LLM
from openhands.memory.utils import parse_summary_response
from openhands.utils.prompt import PromptManager


class MemoryCondenser:
    def __init__(self, llm: LLM, prompt_manager: PromptManager):
        self.llm = llm
        self.prompt_manager = prompt_manager

        # just easier to read
        self.context_window = llm.config.max_input_tokens

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
        assert (
            self.context_window is not None and self.context_window > 2000
        ), 'context window must be a number over 2000'

        # don't condense if under the token limit
        total_token_count = self.llm.get_token_count(messages)
        if total_token_count < self.context_window:
            logger.debug(
                f'Not condensing messages because token count ({total_token_count}) is less than max input tokens ({self.context_window})'
            )
            return AgentSummarizeAction(end_id=-1)

        # calculate safe token limit for processing (e.g. 80% of context window)
        safe_token_limit = int(
            self.context_window * self.llm.config.message_summary_warning_level
        )

        # collect condensable messages with their IDs and token counts
        condensable_messages: list[tuple[Message, int]] = [
            (msg, self.llm.get_token_count([msg.model_dump()]))
            for msg in messages
            if msg.condensable
        ]

        if len(condensable_messages) <= 1:
            # prevents potential infinite loop of summarizing the same message repeatedly
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(condensable_messages)} <= 1]"
            )

        # track the very first message's id - this will be our start_id
        first_message_id = condensable_messages[0][0].event_id

        # create chunks that fit within safe_token_limit
        chunks: list[list[Message]] = []
        current_chunk: list[Message] = []
        current_chunk_tokens = 0

        for msg, token_count in condensable_messages:
            if current_chunk_tokens + token_count > safe_token_limit:
                if current_chunk:  # save current chunk if not empty, it's done
                    chunks.append(current_chunk)

                # start a new chunk
                current_chunk = [msg]
                current_chunk_tokens = token_count
            else:
                # add to current chunk
                current_chunk.append(msg)
                current_chunk_tokens += token_count

        # add the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        # process chunks
        final_summary = None
        # track the last real message id (note: not summary actions)
        last_real_message_id = condensable_messages[-1][0].event_id

        for i, chunk in enumerate(chunks):
            if final_summary:
                # prepend previous summary to next chunk
                summary_message = Message(
                    role='user',
                    content=[TextContent(text=f'Previous summary:\n{final_summary}')],
                    condensable=True,
                    # Note: summary messages don't have an event_id
                    event_id=-1,
                )
                chunk.insert(0, summary_message)

            action_response = self._summarize_messages(chunk)
            summary_action = parse_summary_response(action_response)
            final_summary = summary_action.summary

        # create final summary action
        assert final_summary is not None, 'final summary must not be None here'
        return AgentSummarizeAction(
            summary=final_summary,
            start_id=first_message_id,
            end_id=last_real_message_id,
        )

    def _summarize_messages(self, message_sequence_to_summarize: list[Message]) -> str:
        """Summarize a message sequence using LLM"""
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
        return response.choices[0].message.content
