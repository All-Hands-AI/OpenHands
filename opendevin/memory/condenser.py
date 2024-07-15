from opendevin.core.logger import opendevin_logger as logger
from opendevin.llm.llm import LLM

from .prompts import (
    MESSAGE_SUMMARY_WARNING_FRAC,
    SUMMARY_PROMPT_SYSTEM,
    parse_summary_response,
)


class MemoryCondenser:
    def __init__(self, llm: LLM):
        self.llm = llm

    def condense(self, summarize_prompt: str, llm: LLM):
        """
        Attempts to condense the monologue by using the llm

        Parameters:
        - llm (LLM): llm to be used for summarization

        Raises:
        - Exception: the same exception as it got from the llm or processing the response
        """

        try:
            messages = [{'content': summarize_prompt, 'role': 'user'}]
            resp = llm.completion(messages=messages)
            summary_response = resp['choices'][0]['message']['content']
            return summary_response
        except Exception as e:
            logger.error('Error condensing thoughts: %s', str(e), exc_info=False)

            # TODO If the llm fails with ContextWindowExceededError, we can try to condense the monologue chunk by chunk
            raise

    def _format_summary_history(self, message_history: list[dict]):
        # TODO use existing prompt formatters for this (eg ChatML)
        return '\n'.join([f'{m["role"]}: {m["content"]}' for m in message_history])

    def summarize_messages(self, message_sequence_to_summarize: list[dict]):
        """Summarize a message sequence using LLM"""
        context_window = self.llm.max_input_tokens
        summary_prompt = SUMMARY_PROMPT_SYSTEM
        summary_input = self._format_summary_history(message_sequence_to_summarize)
        summary_input_tkns = self.llm.get_token_count(summary_input)

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

        response = self.llm.completion(
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
