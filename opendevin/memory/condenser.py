from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.agent import (
    AgentDelegateSummaryAction,
)
from opendevin.events.event import Event
from opendevin.events.serialization.event import event_to_memory
from opendevin.llm.llm import LLM
from opendevin.memory.prompts import (
    get_delegate_summarize_prompt,
    parse_delegate_summary_response,
)

MAX_USER_MESSAGE_CHAR_COUNT = 200  # max char count for user messages


class MemoryCondenser:
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

    def summarize_delegate(
        self, delegate_events: list[Event], delegate_agent: str, delegate_task: str
    ) -> AgentDelegateSummaryAction:
        """
        Summarizes the given list of events into a concise summary.

        Parameters:
        - delegate_events: List of events of the delegate.
        - delegate_agent: The agent that was delegated to.
        - delegate_task: The task that was delegated.

        Returns:
        - The summary of the delegate's activities.
        """
        try:
            event_dicts = [event_to_memory(event) for event in delegate_events]
            prompt = get_delegate_summarize_prompt(
                event_dicts, delegate_agent, delegate_task
            )

            messages = [{'role': 'user', 'content': prompt}]
            response = self.llm.completion(messages=messages)

            action_response: str = response['choices'][0]['message']['content']
            action = parse_delegate_summary_response(action_response)
            action.task = delegate_task
            action.agent = delegate_agent
            return action
        except Exception as e:
            logger.error(f'Failed to summarize delegate events: {e}')
            raise
