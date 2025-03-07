from __future__ import annotations

from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.llm import LLM
from openhands.memory.condenser.condenser import RollingCondenser


class LLMSummarizingCondenser(RollingCondenser):
    """A condenser that summarizes forgotten events.

    Maintains a condensed history and forgets old events when it grows too large,
    keeping a special summarization event after the prefix that summarizes all previous summarizations
    and newly forgotten events.
    """

    def __init__(self, llm: LLM, max_size: int = 100, keep_first: int = 1):
        if keep_first >= max_size // 2:
            raise ValueError(
                f'keep_first ({keep_first}) must be less than half of max_size ({max_size})'
            )
        if keep_first < 0:
            raise ValueError(f'keep_first ({keep_first}) cannot be negative')
        if max_size < 1:
            raise ValueError(f'max_size ({max_size}) cannot be non-positive')

        self.max_size = max_size
        self.keep_first = keep_first
        self.llm = llm

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Apply the amortized forgetting strategy with LLM summarization to the given list of events."""
        if len(events) <= self.max_size:
            return events

        head = events[: self.keep_first]

        target_size = self.max_size // 2
        events_from_tail = target_size - len(head)
        tail = events[-events_from_tail:]

        summary_event = (
            events[self.keep_first]
            if isinstance(events[self.keep_first], AgentCondensationObservation)
            else AgentCondensationObservation('No events summarized')
        )

        # Identify events to be forgotten (those not in head or tail)
        forgotten_events = []
        for event in events[self.keep_first : -events_from_tail]:
            if not isinstance(event, AgentCondensationObservation):
                forgotten_events.append(event)

        # Construct prompt for summarization
        prompt = """You are maintaining state history for an LLM-based code agent. Track:

USER_CONTEXT: (Preserve essential user requirements, problem descriptions, and clarifications in concise form)

STATE: {File paths, function signatures, data structures}
TESTS: {Failing cases, error messages, outputs}
CHANGES: {Code edits, variable updates}
DEPS: {Dependencies, imports, external calls}
INTENT: {Why changes were made, acceptance criteria}

PRIORITIZE:
1. Capture key user requirements and constraints
2. Maintain critical problem context
3. Keep all sections concise

SKIP: {Git clones, build logs, file listings}

Example history format:
USER_CONTEXT: Fix FITS card float representation - "0.009125" becomes "0.009124999999999999" causing comment truncation. Use Python's str() when possible while maintaining FITS compliance.

STATE: mod_float() in card.py updated
TESTS: test_format() passed
CHANGES: str(val) replaces f"{val:.16G}"
DEPS: None modified
INTENT: Fix precision while maintaining FITS compliance"""

        prompt + '\n\n'

        prompt += ('\n' + summary_event.message + '\n') if summary_event.message else ''

        prompt + '\n\n'

        for forgotten_event in forgotten_events:
            prompt += str(forgotten_event) + '\n\n'

        response = self.llm.completion(
            messages=[
                {
                    'content': prompt,
                    'role': 'user',
                },
            ],
        )
        summary = response.choices[0].message.content

        self.add_metadata('response', response.model_dump())
        self.add_metadata('metrics', self.llm.metrics.get())

        return head + [AgentCondensationObservation(summary)] + tail

    @classmethod
    def from_config(
        cls, config: LLMSummarizingCondenserConfig
    ) -> LLMSummarizingCondenser:
        return LLMSummarizingCondenser(
            llm=LLM(config=config.llm_config),
            max_size=config.max_size,
            keep_first=config.keep_first,
        )


LLMSummarizingCondenser.register_config(LLMSummarizingCondenserConfig)
