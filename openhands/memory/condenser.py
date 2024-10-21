import json
import os
from pathlib import Path

from openhands.core.config.utils import get_llm_config_arg, load_app_config
from openhands.core.exceptions import SummarizeError
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import AgentSummarizeAction
from openhands.llm.llm import LLM
from openhands.memory.utils import parse_summary_response
from openhands.utils.prompt import PromptManager

WORD_LIMIT = 200
MESSAGE_SUMMARY_WARNING_FRACTION = 0.75


class MemoryCondenser:
    def __init__(self, llm: LLM, prompt_manager: PromptManager):
        self.llm = llm
        self.prompt_manager = prompt_manager

    def condense(
        self,
        messages: list[Message],
    ):
        # Start past the system message, and example messages.,
        # and collect messages for summarization until we reach the desired truncation token fraction (eg 50%)
        # Do not allow truncation  for in-context examples of function calling
        token_counts = [
            self.llm.get_token_count([message.model_dump()])  # type: ignore
            for message in messages
            if message.condensable
        ]
        message_buffer_token_count = sum(token_counts)  # no system and example message

        desired_token_count_to_summarize = int(
            message_buffer_token_count
            * self.llm.config.message_summary_trunc_tokens_fraction  # type: ignore
        )

        candidate_messages_to_summarize = []
        tokens_so_far = 0
        for message in messages:
            if message.condensable:
                logger.debug(
                    f'condensable message: {message.event_id}: {str(message.content)[30:]}'
                )
                candidate_messages_to_summarize.append(message)
                tokens_so_far += self.llm.get_token_count([message.model_dump()])  # type: ignore
            if tokens_so_far > desired_token_count_to_summarize:
                last_summarized_event_id = message.event_id
                break

        logger.debug(
            f'message_summary_trunc_tokens_fraction={self.llm.config.message_summary_trunc_tokens_fraction}'  # type: ignore
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

        action_response = self.summarize_messages(
            message_sequence_to_summarize=message_sequence_to_summarize
        )
        summary_action: AgentSummarizeAction = parse_summary_response(action_response)
        summary_action.end_id = (
            last_summarized_event_id if last_summarized_event_id else -1
        )
        return summary_action

    def _format_summary_history(self, message_history: list[dict]) -> str:
        # TODO use existing prompt formatters for this (eg ChatML)
        return '\n'.join([f'{m["role"]}: {m["content"]}' for m in message_history])

    def summarize_messages(self, message_sequence_to_summarize: list[Message]):
        """Summarize a message sequence using LLM"""
        context_window = self.llm.config.max_input_tokens
        summary_prompt = self.prompt_manager.summarize_template.render()
        summary_input = self._format_summary_history(
            self.llm.format_messages_for_llm(message_sequence_to_summarize)
        )
        summary_input_tkns = self.llm.get_token_count(summary_input)
        if context_window is None:
            raise ValueError('context_window should not be None')
        if summary_input_tkns > MESSAGE_SUMMARY_WARNING_FRACTION * context_window:
            trunc_ratio = (
                MESSAGE_SUMMARY_WARNING_FRACTION * context_window / summary_input_tkns
            ) * 0.8  # For good measure...
            cutoff = int(len(message_sequence_to_summarize) * trunc_ratio)
            curr_summary = self.summarize_messages(
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

        message_sequence = []
        message_sequence.append(
            Message(role='system', content=[TextContent(text=summary_prompt)])
        )
        message_sequence.append(
            Message(role='user', content=[TextContent(text=summary_input)])
        )

        response = self.llm.completion(
            messages=message_sequence,
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

    @staticmethod
    def main():
        """
        Main method for quick testing and debugging.
        Reads the latest debug_summary.json file from the ./logs directory,
        deserializes the messages, and prints them.
        """
        log_dir = Path('./logs')
        log_files = list(log_dir.glob('debug_summary*.json'))

        if not log_files:
            print('No debug_summary.json files found in the ./logs directory.')
            return

        # Sort files to find the latest one based on the numerical suffix
        def extract_suffix(file_path: Path) -> int:
            try:
                suffix = file_path.stem.split('_')[-1]
                return int(suffix) if suffix.isdigit() else 0
            except (IndexError, ValueError):
                return 0

        log_files.sort(key=extract_suffix, reverse=True)
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
    llm = LLM(config=llm_config)
    prompt_manager = PromptManager(
        prompt_dir=os.path.join(
            os.path.dirname(__file__), '..', 'agenthub', 'memcodeact_agent', 'prompts'
        ),
        agent_skills_docs='',
    )
    condenser = MemoryCondenser(llm=llm, prompt_manager=prompt_manager)
    condenser.main()
