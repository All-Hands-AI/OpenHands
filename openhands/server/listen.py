import os

import socketio
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

if os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    # httpx instrumentation need start before any httpx client is created
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()

from openhands.server.app import app as base_app  # noqa
from openhands.server.listen_socket import sio  # noqa
from openhands.server.middleware import (  # noqa
    AttachConversationMiddleware,
    CacheControlMiddleware,
    InMemoryRateLimiter,
    JWTAuthMiddleware,
    ProviderTokenMiddleware,
    RateLimitMiddleware,
)

base_app.middleware('http')(AttachConversationMiddleware(base_app))

# Add middleware to the base app - need to be added before the other middlewares

# TODO: If the run mode is DEV, skip the check
# os.getenv('RUN_MODE') != 'DEV' and base_app.add_middleware(
#     CheckUserActivationMiddleware
# )
base_app.add_middleware(JWTAuthMiddleware)


origin_str = os.getenv('ALLOW_ORIGIN')
if not origin_str:
    origin_str = '*'

origins = [i for i in origin_str.split(',')]
print('origins', origins)
base_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

base_app.add_middleware(CacheControlMiddleware)
base_app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=InMemoryRateLimiter(requests=1000, seconds=1),
)
base_app.middleware('http')(ProviderTokenMiddleware(base_app))

app = socketio.ASGIApp(sio, other_asgi_app=base_app)

if os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.threading import ThreadingInstrumentor
    from traceloop.sdk import Traceloop

    FastAPIInstrumentor.instrument_app(base_app)
    AsyncioInstrumentor().instrument()
    ThreadingInstrumentor().instrument()

    if os.getenv('TRACELOOP_BASE_URL'):
        Traceloop.init(
            disable_batch=False, app_name=os.getenv('OTEL_SERVICE_NAME', 'openhands')
        )
