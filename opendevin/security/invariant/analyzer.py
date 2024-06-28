from dataclasses import asdict
from typing import Optional

from invariant import Monitor

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action, ActionSecurityRisk
from opendevin.events.event import Event
from opendevin.events.observation import Observation
from opendevin.events.stream import EventStream
from opendevin.security.analyzer import SecurityAnalyzer
from opendevin.security.invariant.parser import TraceElement, parse_element
from opendevin.security.invariant.policies import DEFAULT_INVARIANT_POLICY


class InvariantAnalyzer(SecurityAnalyzer):
    """Security analyzer based on Invariant."""

    trace: list[TraceElement]
    input: list[dict]

    def __init__(self, event_stream: EventStream, policy: Optional[str] = None):
        """Initializes a new instance of the InvariantAnalzyer class."""
        super().__init__(event_stream)
        self.trace = []
        self.input = []
        if policy is None:
            policy = DEFAULT_INVARIANT_POLICY
        self.monitor = Monitor.from_string(policy)

    def print_trace(self):
        logger.info('-> Invariant trace:')
        for element in self.trace:
            logger.info('\t-> ' + str(element))

    async def log_event(self, event: Event) -> None:
        if isinstance(event, Observation):
            element = parse_element(self.trace, event)
            self.trace.extend(element)
            self.input.extend([asdict(e) for e in element])  # type: ignore [call-overload]
        else:
            logger.info('Invariant skipping element: event')
        self.print_trace()

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        logger.info('Calling security_risk on InvariantAnalyzer')
        new_elements = parse_element(self.trace, event)
        self.trace.extend(new_elements)
        # input = [asdict(e) for e in self.trace]
        self.input.extend([asdict(e) for e in new_elements])  # type: ignore [call-overload]
        errors = self.monitor.check(self.input)
        logger.info('policy result:')
        logger.info('errors: ' + str(errors))
        if len(errors) > 0:
            return ActionSecurityRisk.MEDIUM
        else:
            return ActionSecurityRisk.LOW
