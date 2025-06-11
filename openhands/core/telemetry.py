"""
OpenHands Telemetry Module.

This module provides integration with OpenTelemetry and Logfire for comprehensive
logging, tracing, and metrics collection in the OpenHands agent framework.
"""

import json
import os
from typing import Any, Mapping, Optional, Sequence, Union

import logfire
from logfire.propagate import ContextCarrier
from opentelemetry._logs import LogRecord
from opentelemetry._logs.severity import SeverityNumber
from opentelemetry.trace import (
    NoOpTracer,
    Span,
    get_tracer_provider,
    use_span,
)
from opentelemetry.trace.span import TraceFlags
from opentelemetry.util.types import Attributes
from pydantic import TypeAdapter

from openhands.core import logger
from openhands.core.config.telemetry_config import TelemetryConfig

ANY_ADAPTER = TypeAdapter[Any](Any)

AnyValue = Union[
    str,
    bool,
    int,
    float,
    bytes,
    Sequence['AnyValue'],
    Mapping[str, 'AnyValue'],
    None,
]


def serialize_any(value: Any) -> str:
    try:
        return ANY_ADAPTER.dump_python(value, mode='json')
    except Exception:
        try:
            return str(value)
        except Exception as e:
            return f'Unable to serialize: {e}'


class Event(LogRecord):
    def __init__(
        self,
        name: str,
        timestamp: Optional[int] = None,
        trace_id: Optional[int] = None,
        span_id: Optional[int] = None,
        trace_flags: Optional['TraceFlags'] = None,
        body: AnyValue = None,
        severity_number: Optional[SeverityNumber] = None,
        attributes: Optional[Attributes] = None,
    ):
        attributes = attributes or {}
        event_attributes = {
            **attributes,
            'event.name': name,
        }
        super().__init__(
            timestamp=timestamp,
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags,
            body=body,
            severity_number=severity_number,
            attributes=event_attributes,
        )
        self.name = name

    def event_to_dict(self) -> dict[str, Any]:
        if not self.body:
            body = {}  # type: ignore
        elif isinstance(self.body, Mapping):
            body = self.body  # type: ignore
        else:
            body = {'body': self.body}
        return {**body, **(self.attributes or {})}


class TelemetryManager:
    """
    Manager class for telemetry common operations

    See the [Debugging and Monitoring guide](https://ai.pydantic.dev/logfire/) for more info.
    """

    def __init__(self, config: TelemetryConfig):
        """
        Initialize the TelemetryManager.

        Args:
            config: TelemetryConfig
        """
        self.config = config
        self.tracer = NoOpTracer()

        if config.logfire_enabled:
            # The logfire_token is prioritized to be obtained from the configuration. If not, it will be retrieved from the LOGFIRE_TOKEN env.
            logfire_token = config.logfire_token
            if not logfire_token:
                logger.openhands_logger.debug('retrive logfire_token from env')
                logfire_token = os.getenv('LOGFIRE_TOKEN', '')
                if not logfire_token:
                    logger.openhands_logger.warning(
                        'The logfire_token has not been obtained. Please configure it in the config toml or set the environment variable LOGFIRE_TOKEN.'
                    )
                    return

            tracer_provider = get_tracer_provider()
            self.tracer = tracer_provider.get_tracer(
                config.service_name, config.service_version
            )

            logfire.configure(
                token=logfire_token,
                scrubbing=config.logfire_scrubbing,
            )

    def messages_to_otel_event(self, messages: list) -> list[Event]:
        """
        Convert messages to a list of OpenTelemetry events.
        Args:
            messages: The message list.
        Returns:
            List of OpenTelemetry events.
        """
        events: list[Event] = []
        for msg_idx, message in enumerate(messages):
            content = message.get('content')
            role = message.get('role')
            events.append(
                Event('gen_ai.user.message', body={'content': content, 'role': role})
            )

        for event in events:
            event.body = serialize_any(event.body)
        return events

    def emit_events(self, span: Span, events: list[Event]) -> None:
        attr_name = 'events'
        span.set_attributes(
            {
                attr_name: json.dumps([event.event_to_dict() for event in events]),
                'logfire.json_schema': json.dumps(
                    {
                        'type': 'object',
                        'properties': {
                            attr_name: {'type': 'array'},
                        },
                    }
                ),
            }
        )

    def log_span(self, name: str, attributes: Attributes) -> None:
        with self.tracer.start_as_current_span(name) as span:
            span.set_attributes(attributes)

    def start_span(
        self,
        span_name: str,
        attributes: Attributes | None = None,
        parent_span: Optional[ContextCarrier] = None,
    ):
        """Manually start a span"""
        if parent_span is not None:
            with use_span(parent_span):
                with self.tracer.start_span(span_name, attributes=attributes) as span:
                    return span

        with self.tracer.start_span(span_name, attributes=attributes) as span:
            return span
