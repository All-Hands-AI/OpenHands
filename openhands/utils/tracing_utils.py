import json
import os
from functools import wraps
from typing import Optional

from opentelemetry import context as context_api
from opentelemetry import trace
from opentelemetry.semconv.ai import SpanAttributes, TraceloopSpanKindValues
from traceloop.sdk.telemetry import Telemetry
from traceloop.sdk.tracing import get_tracer, set_workflow_name
from traceloop.sdk.tracing.tracing import (
    TracerWrapper,
    get_chained_entity_name,
    set_entity_name,
)
from traceloop.sdk.utils.json_encoder import JSONEncoder


def _should_send_prompts():
    return (
        os.getenv('TRACELOOP_TRACE_CONTENT') or 'true'
    ).lower() == 'true' or context_api.get_value('override_enable_content_tracing')


def streaming_llm_workflow(
    name: Optional[str] = None,
    version: Optional[int] = None,
    tlp_span_kind: Optional[TraceloopSpanKindValues] = TraceloopSpanKindValues.WORKFLOW,
):
    return streaming_entity_method(
        name=name, version=version, tlp_span_kind=tlp_span_kind
    )


def streaming_entity_method(
    name: Optional[str] = None,
    version: Optional[int] = None,
    tlp_span_kind: Optional[TraceloopSpanKindValues] = TraceloopSpanKindValues.TASK,
):
    def decorate(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            if not TracerWrapper.verify_initialized():
                return fn(*args, **kwargs)

            entity_name = name or fn.__name__
            if tlp_span_kind in [
                TraceloopSpanKindValues.WORKFLOW,
                TraceloopSpanKindValues.AGENT,
            ]:
                set_workflow_name(entity_name)
            if tlp_span_kind:
                span_name = f'{entity_name}.{tlp_span_kind.value}'

            with get_tracer() as tracer:
                span = tracer.start_span(span_name)
                ctx = trace.set_span_in_context(span)
                context_api.attach(ctx)

                if tlp_span_kind in [
                    TraceloopSpanKindValues.TASK,
                    TraceloopSpanKindValues.TOOL,
                ]:
                    chained_entity_name = get_chained_entity_name(entity_name)
                    set_entity_name(chained_entity_name)
                else:
                    chained_entity_name = entity_name

                if tlp_span_kind:
                    span.set_attribute(
                        SpanAttributes.TRACELOOP_SPAN_KIND,
                        tlp_span_kind.value,
                    )
                span.set_attribute(
                    SpanAttributes.TRACELOOP_ENTITY_NAME, chained_entity_name
                )
                if version:
                    span.set_attribute(SpanAttributes.TRACELOOP_ENTITY_VERSION, version)

                try:
                    if _should_send_prompts():
                        span.set_attribute(
                            SpanAttributes.TRACELOOP_ENTITY_INPUT,
                            json.dumps(
                                {'args': args, 'kwargs': kwargs}, cls=JSONEncoder
                            ),
                        )
                except TypeError as e:
                    Telemetry().log_exception(e)

                res = fn(*args, **kwargs)

                try:
                    if _should_send_prompts():
                        span.set_attribute(
                            SpanAttributes.TRACELOOP_ENTITY_OUTPUT,
                            json.dumps(res, cls=JSONEncoder),
                        )
                except TypeError as e:
                    Telemetry().log_exception(e)

                return res

        return wrap

    return decorate
