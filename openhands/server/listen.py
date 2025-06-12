import os

import socketio

from openhands.server.app import app as base_app
from openhands.server.runtime_startup import initialize_runtime_on_startup
from openhands.server.listen_socket import sio
from openhands.server.middleware import (
    CacheControlMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
)
from openhands.server.static import SPAStaticFiles

if os.getenv('SERVE_FRONTEND', 'true').lower() == 'true':
    base_app.mount(
        '/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist'
    )

base_app.add_middleware(LocalhostCORSMiddleware)
base_app.add_middleware(CacheControlMiddleware)
base_app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=InMemoryRateLimiter(requests=10, seconds=1),
)

# Initialize runtime system for Railway deployment
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('LOCAL_RUNTIME_MODE'):
    initialize_runtime_on_startup()

app = socketio.ASGIApp(sio, other_asgi_app=base_app)
