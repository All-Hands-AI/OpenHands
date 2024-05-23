from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action
from opendevin.events.event import EventSource
from opendevin.events.observation.observation import Observation
from opendevin.events.observation.summary import SummaryObservation
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
    ) -> list[tuple[Action, Observation]]:
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
        condensed_events = []
        chunk: list[tuple[Action, Observation]] = []

        for action, observation in events:
            if action.source == EventSource.USER:
                # event.should_condense = False
                condensed_events.append((action, observation))
                if chunk:
                    # Summarize the previous chunk
                    actions, summary_observation = self._summarize_chunk(chunk)
                    if actions and summary_observation:
                        assert isinstance(
                            summary_observation, SummaryObservation
                        )  # FIXME we don't actually want assert
                        summary_observation._source = EventSource.USER  # type: ignore [attr-defined]
                        condensed_events.append((action, summary_observation))
                    chunk = []
            elif hasattr(action, 'priority') and getattr(action, 'priority') == 'high':
                condensed_events.append((action, observation))
                if chunk:
                    # Summarize the previous chunk
                    actions, summary_observation = self._summarize_chunk(chunk)
                    if actions and summary_observation:
                        assert isinstance(summary_observation, SummaryObservation)
                        summary_observation._source = (EventSource.USER,)  # type: ignore [attr-defined]
                        condensed_events.append((action, summary_observation))
                    chunk = []
            chunk.append((action, observation))

        # Summarize the last chunk if any
        if chunk:
            actions, summary_observation = self._summarize_chunk(chunk)
            if actions and summary_observation:
                assert isinstance(summary_observation, SummaryObservation)
                summary_observation._source = EventSource.USER  # type: ignore [attr-defined]
                condensed_events.append((action, summary_observation))

        return condensed_events

    def _summarize_chunk(
        self, chunk: list[tuple[Action, Observation]]
    ) -> tuple[Action, Observation]:
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
                - "action": "Summarize"
                - "content": A comma-separated list of all the action names from the provided actions
                - "summary": A single sentence summarizing all the provided observations

                {chunk}
            """
            messages = [{'role': 'user', 'content': prompt}]
            response = self.llm.do_completion(messages=messages)
            action, observation = parse_summary_response(response)
            return action, observation
        except Exception as e:
            logger.error(f'Failed to summarize chunk: {e}')

        raise Exception  # could return NullAction / NullObservation... and ignore them, or just some exception

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
