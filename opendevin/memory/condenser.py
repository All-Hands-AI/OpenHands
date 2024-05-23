from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.event import Event, EventSource
from opendevin.events.observation.summary import SummaryObservation
from opendevin.llm.llm import LLM

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
        max_context_limit: int | None = None,
    ):
        """
        Initialize the MemoryCondenser.

        llm is the language model to use for summarization.
        max_context_limit is an optional integer specifying the maximum context limit for the LLM.
        If not provided, the condenser will act lazily and only condense when a context window limit error occurs.

        Parameters:
        - llm: The language model to use for summarization.
        - max_context_limit: Optional integer specifying the maximum context limit for the LLM.
        """
        self.llm = llm
        self.max_context_limit = max_context_limit

    def condense(
        self,
        events: list[Event],
    ) -> list[Event]:
        """
        Condenses the given list of events using the llm. Returns the condensed list of events.

        Condensation heuristics:
        - Keep initial messages (system, user instruction)
        - Prioritize more recent history
        - Lazily summarize between initial instruction and most recent, starting with earliest condensable turns
        - Introduce a SummaryObservation event type for textual summaries
        - Split events into chunks delimited by user message actions, condense each chunk into a sentence

        Parameters:
        - events: List of events to condense.

        Returns:
        - The condensed list of events.
        """
        condensed_events = []
        chunk: list[Event] = []

        for event in events:
            if event.source == EventSource.USER:
                # event.should_condense = False
                condensed_events.append(event)
                if chunk:
                    # Summarize the previous chunk
                    summary = self._summarize_chunk(chunk)
                    summary_observation = SummaryObservation(
                        content=summary,
                        priority='low',
                    )
                    summary_observation._source = EventSource.USER  # type: ignore [attr-defined]
                    condensed_events.append(summary_observation)
                    chunk = []
            elif hasattr(event, 'priority') and getattr(event, 'priority') == 'high':
                condensed_events.append(event)
                if chunk:
                    # Summarize the previous chunk
                    summary = self._summarize_chunk(chunk)
                    summary_observation = SummaryObservation(
                        content=summary,
                        priority='low',
                    )
                    summary_observation._source = (EventSource.USER,)  # type: ignore [attr-defined]
                    condensed_events.append(summary_observation)
                    chunk = []
                chunk.append(event)

        # Summarize the last chunk if needed
        if chunk:
            summary = self._summarize_chunk(chunk)
            summary_observation = SummaryObservation(
                content=summary,
                priority='low',
            )
            summary_observation._source = EventSource.USER  # type: ignore [attr-defined]
            condensed_events.append(summary_observation)

        return condensed_events

    def _summarize_chunk(self, chunk: list[Event]) -> str:
        """
        Summarizes the given chunk of events into a single sentence.

        Parameters:
        - chunk: List of events to summarize.

        Returns:
        - The summary sentence.
        """
        try:
            prompt = f'Please summarize the following events into a single sentence:\n\n{chunk}\n\nSummary:'
            messages = [{'role': 'user', 'content': prompt}]
            response = self.llm.do_completion(messages=messages)
            summary = response['choices'][0]['message']['content']
            return summary
        except Exception as e:
            logger.error(f'Failed to summarize chunk: {e}')
            # TODO: Implement proper error handling logic here.
        return ''  # FIXME should this be an obs directly?

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
