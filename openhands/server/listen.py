import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

import socketio
from fastapi import (
    FastAPI,
)

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.server.middleware import (
    AttachSessionMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    NoCacheMiddleware,
    RateLimitMiddleware,
)
from openhands.server.routes.auth import app as auth_api_router
from openhands.server.routes.conversation import app as conversation_api_router
from openhands.server.routes.feedback import app as feedback_api_router
from openhands.server.routes.files import app as files_api_router
from openhands.server.routes.public import app as public_api_router
from openhands.server.routes.security import app as security_api_router
from openhands.server.socket import sio
from openhands.server.static import SPAStaticFiles

base_app = FastAPI()
base_app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

base_app.add_middleware(NoCacheMiddleware)
base_app.add_middleware(
    RateLimitMiddleware, rate_limiter=InMemoryRateLimiter(requests=10, seconds=1)
)


@base_app.get('/health')
async def health():
    return 'OK'


base_app.include_router(auth_api_router)
base_app.include_router(public_api_router)
base_app.include_router(files_api_router)
base_app.include_router(conversation_api_router)
base_app.include_router(security_api_router)
base_app.include_router(feedback_api_router)

base_app.middleware('http')(
    AttachSessionMiddleware(base_app, target_router=files_api_router)
)
base_app.middleware('http')(
    AttachSessionMiddleware(base_app, target_router=conversation_api_router)
)
base_app.middleware('http')(
    AttachSessionMiddleware(base_app, target_router=security_api_router)
)
base_app.middleware('http')(
    AttachSessionMiddleware(base_app, target_router=feedback_api_router)
)

base_app.mount(
    '/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist'
)

app = socketio.ASGIApp(sio, other_asgi_app=base_app)
