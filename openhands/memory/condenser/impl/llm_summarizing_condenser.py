from __future__ import annotations

from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig
from openhands.core.message import Message, TextContent
from openhands.events.action.agent import CondensationAction
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.llm import LLM
from openhands.memory.condenser.condenser import (
    Condensation,
    RollingCondenser,
    View,
)


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

    def get_view(self, events: list[Event]) -> View:
        result_events = []
        forgotten_event_ids = []

        for event in events:
            if isinstance(event, CondensationAction):
                forgotten_event_ids.extend(event.forgotten_event_ids)
            else:
                result_events.append(event)

        kept_events = [
            event for event in result_events if event.id not in forgotten_event_ids
        ]

        # Grab the latest summary
        summary: str | None = None
        for event in reversed(events):
            if isinstance(event, CondensationAction):
                summary = event.summary
                break

        # If there's a summary event, stick it just after the kept prefix
        if summary is not None:
            return View(
                events=kept_events[: self.keep_first]
                + [AgentCondensationObservation(summary)]
                + kept_events[self.keep_first :]
            )
        else:
            return View(events=kept_events)

    def get_condensation(self, view: View) -> Condensation:
        head = view[: self.keep_first]
        target_size = self.max_size // 2
        # Number of events to keep from the tail -- target size, minus however many
        # prefix events from the head, minus one for the summarization event
        events_from_tail = target_size - len(head) - 1

        summary_event = (
            view[self.keep_first]
            if isinstance(view[self.keep_first], AgentCondensationObservation)
            else AgentCondensationObservation('No events summarized')
        )

        # Identify events to be forgotten (those not in head or tail)
        forgotten_events = []
        for event in view[self.keep_first : -events_from_tail]:
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

        messages = [Message(role='user', content=[TextContent(text=prompt)])]

        response = self.llm.completion(
            messages=self.llm.format_messages_for_llm(messages),
        )
        summary = response.choices[0].message.content

        self.add_metadata('response', response.model_dump())
        self.add_metadata('metrics', self.llm.metrics.get())

        return Condensation(
            action=CondensationAction(
                condenser_cls=self.__class__.__name__,
                forgotten_event_ids=[event.id for event in forgotten_events],
                considered_event_ids=[event.id for event in view],
                summary=summary,
            )
        )

    def should_condense(self, view: View) -> bool:
        return len(view) > self.max_size

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
