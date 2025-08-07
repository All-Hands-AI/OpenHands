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
    IntegrationRateLimitMiddleware,
    JWTAuthMiddleware,
    ProviderTokenMiddleware,
    RateLimitMiddleware,
    UserBasedRateLimiter,
    APIKeyAuthMiddleware,
)
from openhands.server.utils.ratelimit_storage import create_rate_limiter_storage  # noqa


base_app.middleware('http')(AttachConversationMiddleware(base_app))

# Add middleware to the base app - need to be added before the other middlewares

# TODO: If the run mode is DEV, skip the check
# os.getenv('RUN_MODE') != 'DEV' and base_app.add_middleware(
#     CheckUserActivationMiddleware
# )

# Add integration-specific rate limiting
INTEGRATION_RATE_LIMIT_REQUESTS = int(
    os.getenv('INTEGRATION_RATE_LIMIT_REQUESTS') or 10
)
INTEGRATION_RATE_LIMIT_SECONDS = int(os.getenv('INTEGRATION_RATE_LIMIT_SECONDS') or 60)

# Configure rate limiter storage
RATE_LIMITER_STORAGE_TYPE = os.getenv('RATE_LIMITER_STORAGE_TYPE', 'memory')
RATE_LIMITER_HOST_URL = os.getenv('RATE_LIMITER_HOST_URL')
RATE_LIMITER_HOST_PASSWORD = os.getenv('RATE_LIMITER_HOST_PASSWORD')
RATE_LIMITER_KEY_PREFIX = os.getenv('RATE_LIMITER_KEY_PREFIX')

rate_limiter_storage = create_rate_limiter_storage(
    storage_type=RATE_LIMITER_STORAGE_TYPE,
    host_url=RATE_LIMITER_HOST_URL,
    host_password=RATE_LIMITER_HOST_PASSWORD,
    key_prefix=RATE_LIMITER_KEY_PREFIX,
)

integration_rate_limiter = UserBasedRateLimiter(
    requests=INTEGRATION_RATE_LIMIT_REQUESTS,
    seconds=INTEGRATION_RATE_LIMIT_SECONDS,
    sleep_seconds=0,  # Reject immediately instead of sleeping
    storage=rate_limiter_storage,
)
base_app.add_middleware(
    IntegrationRateLimitMiddleware, rate_limiter=integration_rate_limiter
)

base_app.add_middleware(APIKeyAuthMiddleware)
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
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
    from opentelemetry.instrumentation.threading import ThreadingInstrumentor
    from traceloop.sdk import Traceloop

    FastAPIInstrumentor.instrument_app(base_app)
    AsyncioInstrumentor().instrument()
    ThreadingInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()

    if os.getenv('TRACELOOP_BASE_URL'):
        Traceloop.init(
            disable_batch=False, app_name=os.getenv('OTEL_SERVICE_NAME', 'openhands')
        )
