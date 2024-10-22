import json
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from openhands.core.config.utils import get_llm_config_arg, load_app_config
from openhands.core.exceptions import SummarizeError
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import AgentSummarizeAction
from openhands.llm.llm import LLM
from openhands.memory.utils import parse_summary_response
from openhands.utils.prompt import PromptManager

WORD_LIMIT = 200


class MemoryCondenser:
    def __init__(self, llm: LLM, summarize_prompt: Template):
        self.llm = llm
        self.summarize_prompt = summarize_prompt

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
        if self.llm.get_token_count(messages) < self.llm.config.max_input_tokens:
            logger.debug(
                f'Not condensing messages because token count ({self.llm.get_token_count(messages)}) is less than max input tokens ({self.llm.config.max_input_tokens})'
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

        candidate_messages_to_summarize = []
        tokens_so_far = 0
        last_summarized_event_id = -1

        # collect messages until we reach the desired size
        for message in messages:
            if message.condensable:
                logger.debug(
                    f'condensable message: {message.event_id}: {str(message.content)[30:]}'
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

        # Render the template with the message history
        summary_input = self._format_summary_history(
            self.llm.format_messages_for_llm(message_sequence_to_summarize)
        )
        summary_input_tkns = self.llm.get_token_count(summary_input)

        # Check if the token count exceeds the allowed summary level
        if (
            summary_input_tkns
            > self.llm.config.message_summary_warning_level * self.context_window
        ):
            trunc_ratio = (
                self.llm.config.message_summary_warning_level
                * self.context_window
                / summary_input_tkns
            ) * 0.8  # For good measure...
            cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)

            # Recursively summarize the first part to fit within the context window
            curr_summary = self._summarize_messages(
                message_sequence_to_summarize=message_sequence_to_summarize[:cutoff]
            )
            curr_summary_message = (
                'Summary of all Action and Observations till now: \n'
                + curr_summary['summary']
            )
            logger.debug(f'curr_summary_message: {curr_summary_message}')

            curr_summary_message = [TextContent(text=curr_summary_message)]
            input = [
                Message({'role': 'user', 'content': curr_summary_message})
            ] + message_sequence_to_summarize[cutoff:]
            summary_input = self._format_summary_history(
                self.llm.format_messages_for_llm(input)
            )

        # build the message to send
        message = Message(
            role='system', content=[TextContent(text=self.summarize_prompt)]
        )

        response = self.llm.completion(
            messages=[message],
            stop=[
                '</execute_ipython>',
                '</execute_bash>',
                '</execute_browse>',
            ],
            temperature=0.0,
        )

        print(f'summarize_messages got response: {response}')

        # action_response = response['choices'][0]['message']['content']
        return response

    def _save_messages_for_debugging(
        self, messages: list[Message], summary_action: AgentSummarizeAction
    ) -> None:
        """
        Serializes the list of Message objects and the summary action,
        then saves them to a JSON file in the ./logs directory for debugging purposes.

        Args:
            messages (list[Message]): The list of messages to serialize.
            summary_action (AgentSummarizeAction): The summary action to append.
        """
        # Ensure the logs directory exists
        log_dir = Path('./logs')
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate a timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'debug_summary_{timestamp}.json'
        file_path = log_dir / filename

        try:
            # Serialize messages using Pydantic's model_dump()
            serialized_messages = [message.model_dump() for message in messages]

            # Create a Message instance for the summary_action
            summary_event = Message(
                role='assistant', content=[TextContent(text=str(summary_action))]
            )
            serialized_summary = summary_event.model_dump()

            # Append the serialized summary to the messages
            serialized_messages.append(serialized_summary)

            with file_path.open('w', encoding='utf-8') as f:
                json.dump(serialized_messages, f, ensure_ascii=False, indent=4)

            logger.debug(f'Messages successfully saved to {file_path}')
        except Exception as e:
            logger.error(f'Failed to save messages for debugging: {e}')

    @staticmethod
    def main():
        """
        Main method for quick testing and debugging.
        Reads the latest debug_summary_<timestamp>.json file from the ./logs directory,
        deserializes the messages, and prints them.
        """
        log_dir = Path('./logs')
        log_files = list(log_dir.glob('debug_summary_*.json'))

        if not log_files:
            print(
                'No debug_summary_<timestamp>.json files found in the ./logs directory.'
            )
            return

        # Sort files to find the latest one based on the timestamp in the filename
        def extract_timestamp(file_path: Path) -> datetime:
            try:
                # Extract the timestamp part from the filename
                timestamp_str = file_path.stem.split('_')[-1]
                return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            except (IndexError, ValueError):
                # If timestamp parsing fails, assign the earliest possible datetime
                return datetime.min

        log_files.sort(key=extract_timestamp, reverse=True)
        latest_log = log_files[0]

        print(f'Loading messages from: {latest_log}')

        try:
            with latest_log.open('r', encoding='utf-8') as f:
                messages_data = json.load(f)

            # Deserialize messages using Pydantic's parse_obj
            messages: list[Message] = [
                Message.parse_obj(msg_dict) for msg_dict in messages_data
            ]

            print(f'Successfully loaded {len(messages)} messages:')
            for msg in messages:
                print(f'Role: {msg.role}, Content: {msg.content}')
        except Exception as e:
            print(f'An error occurred while reading {latest_log}: {e}')


if __name__ == '__main__':
    # Initialize dependencies as needed for testing
    app_config = load_app_config()
    llm_config = get_llm_config_arg('deepseek')
    if llm_config is not None:
        llm = LLM(config=llm_config)
    else:
        llm = LLM(app_config.get_llm_config('llm'))

    prompt_manager = PromptManager(
        prompt_dir=os.path.join(
            os.path.dirname(__file__), '..', 'agenthub', 'memcodeact_agent', 'prompts'
        ),
        agent_skills_docs='',
    )
    condenser = MemoryCondenser(
        llm=llm, summarize_prompt=prompt_manager.summarize_template
    )
    condenser.main()
