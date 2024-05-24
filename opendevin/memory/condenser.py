from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.event import EventSource
from opendevin.events.observation.observation import Observation
from opendevin.llm.llm import LLM
from opendevin.memory.prompts import parse_summary_response

MAX_TOKEN_COUNT_PADDING = (
    512  # estimation of tokens to add to the prompt for the max token count
)


class MemoryCondenser:
    """
    Condenses the prompt with a call to the LLM.
    """

    def __init__(
        self,
        llm: LLM,
    ):
        """
        Initialize the MemoryCondenser.

        llm is the language model to use for summarization.
        config.max_input_tokens is an optional configuration setting specifying the maximum context limit for the LLM.
        If not provided, the condenser will act lazily and only condense when a context window limit error occurs.

        Parameters:
        - llm: The language model to use for summarization.
        """
        self.llm = llm

    def condense(
        self,
        events: list[tuple[Action, Observation]],
    ) -> AgentSummarizeAction | None:
        """
        Condenses the given list of events using the llm. Returns the condensed list of events.

        Condensation heuristics:
        - Keep initial messages (system, user message setting task)
        - Prioritize more recent history
        - Lazily summarize between initial instruction and most recent, starting with earliest condensable turns
        - Introduce a SummaryObservation event type for textual summaries
        - Split events into chunks delimited by user message actions (messages with EventSource.USER), condense each chunk into a sentence

        Parameters:
        - events: List of events to condense.

        Returns:
        - The condensed list of events.
        """
        # chunk of (action, observation) to summarize
        chunk: list[tuple[Action, Observation]] = []
        chunk_start_index = 0

        for i, (action, observation) in enumerate(events):
            if action.source == EventSource.USER:
                if chunk:
                    summary_action = self._summarize_chunk(chunk)
                    summary_action._chunk_start = chunk_start_index
                    summary_action._chunk_end = i
                    return summary_action
                else:
                    chunk_start_index = i + 1
            elif hasattr(action, 'priority') and getattr(action, 'priority') == 'high':
                if chunk:
                    summary_action = self._summarize_chunk(chunk)
                    summary_action._chunk_start = chunk_start_index
                    summary_action._chunk_end = i
                    return summary_action
                else:
                    chunk_start_index = i + 1
            else:
                chunk.append((action, observation))

        if chunk:
            summary_action = self._summarize_chunk(chunk)
            summary_action._chunk_start = chunk_start_index
            summary_action._chunk_end = len(events)
            return summary_action
        else:
            return None

    def _summarize_chunk(
        self, chunk: list[tuple[Action, Observation]]
    ) -> AgentSummarizeAction:
        """
        Summarizes the given chunk of events into a single sentence.

        Parameters:
        - chunk: List of events to summarize.

        Returns:
        - The summary sentence.
        """
        try:
            prompt = f"""
            Given the following actions and observations, create a JSON response with:
                - "action_type": "SUMMARIZE"
                - "actions": A comma-separated list of all the action names from the provided actions
                - "summary": A single sentence summarizing all the provided observations

                {chunk}
            """
            messages = [{'role': 'user', 'content': prompt}]
            response = self.llm.do_completion(messages=messages)
            action = parse_summary_response(response)
            return action
        except Exception as e:
            logger.error(f'Failed to summarize chunk: {e}')
            raise Exception

    def _estimate_token_count(self, events: list[dict]) -> int:
        """
        Estimates the token count of the given events using a rough tokenizer.

        Parameters:
        - events: List of events to estimate the token count for.

        Returns:
        - Estimated token count.
        """
        token_count = 0
        for event in events:
            token_count += len(event['content'].split())
        return token_count + MAX_TOKEN_COUNT_PADDING
