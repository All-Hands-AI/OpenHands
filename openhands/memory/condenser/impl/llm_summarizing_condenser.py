from __future__ import annotations

from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.llm import LLM
from openhands.memory.condenser.condenser import Condenser


class LLMSummarizingCondenser(Condenser):
    """A condenser that relies on a language model to summarize the event sequence as a single event."""

    def __init__(self, llm: LLM):
        self.llm = llm

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Applies an LLM to summarize the list of events.

        Raises:
            Exception: If the LLM is unable to summarize the event sequence.
        """
        try:
            # Convert events to a format suitable for summarization
            events_text = '\n'.join(f'{e.timestamp}: {e.message}' for e in events)
            summarize_prompt = f'Please summarize these events:\n{events_text}'

            resp = self.llm.completion(
                messages=[{'content': summarize_prompt, 'role': 'user'}]
            )
            summary_response = resp.choices[0].message.content

            # Create a new summary event with the condensed content
            summary_event = AgentCondensationObservation(summary_response)

            # Add metrics to state
            self.add_metadata('response', resp.model_dump())
            self.add_metadata('metrics', self.llm.metrics.get())

            return [summary_event]

        except Exception as e:
            logger.error(f'Error condensing events: {str(e)}')
            raise e

    @classmethod
    def from_config(
        cls, config: LLMSummarizingCondenserConfig
    ) -> LLMSummarizingCondenser:
        return LLMSummarizingCondenser(llm=LLM(config=config.llm_config))


LLMSummarizingCondenser.register_config(LLMSummarizingCondenserConfig)
