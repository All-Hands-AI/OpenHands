from __future__ import annotations

from openhands.core.config.condenser_config import TokenAwareCondenserConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.message_utils import exceeds_token_limit
from openhands.events.action.agent import CondensationAction
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.llm import LLM
from openhands.memory.condenser.condenser import (
    Condensation,
    RollingCondenser,
    View,
)


class TokenAwareCondenser(RollingCondenser):
    """A condenser that summarizes events when they exceed a token limit.

    Maintains a condensed history and summarizes events when they exceed a token threshold,
    keeping a special summarization event after the prefix that summarizes all previous summarizations
    and newly forgotten events.
    """

    max_input_tokens: int = 32000
    agent_llm: LLM

    def __init__(self, llm: LLM, keep_first: int = 1, threshold: float = 0.85):
        if keep_first < 0:
            raise ValueError(f'keep_first ({keep_first}) cannot be negative')
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(f'threshold ({threshold}) must be between 0.0 and 1.0')

        self.keep_first = keep_first
        self.threshold = threshold
        self.llm = llm

        super().__init__()

    def get_condensation(self, view: View) -> Condensation:
        head = view[: self.keep_first]
        target_size = len(view) // 2
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

        prompt += '\n\n'

        prompt += ('\n' + summary_event.message + '\n') if summary_event.message else ''

        prompt += '\n\n'

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
                forgotten_events_start_id=min(event.id for event in forgotten_events),
                forgotten_events_end_id=max(event.id for event in forgotten_events),
                summary=summary,
                summary_offset=self.keep_first,
            )
        )

    def should_condense(self, view: View) -> bool:
        # Check if we exceed the token limit using the last eligible event
        estimated_tokens = int(self.threshold * self.max_input_tokens)
        logger.debug(f'Estimated max tokens to keep: {estimated_tokens}')

        if exceeds_token_limit(
            view.events,
            self.agent_llm.metrics,
            estimated_tokens,
        ):
            return True
        return False

    @classmethod
    def from_config(cls, config: TokenAwareCondenserConfig) -> TokenAwareCondenser:
        return TokenAwareCondenser(
            llm=LLM(config=config.llm_config),
            keep_first=config.keep_first,
            threshold=config.threshold,
        )


TokenAwareCondenser.register_config(TokenAwareCondenserConfig)
