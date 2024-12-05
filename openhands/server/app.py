import warnings

from openhands.utils.import_utils import import_from

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
)

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.server.middleware import (
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    NoCacheMiddleware,
    RateLimitMiddleware,
)
from openhands.server.routes.conversation import app as conversation_api_router
from openhands.server.routes.feedback import app as feedback_api_router
from openhands.server.routes.files import app as files_api_router
from openhands.server.routes.github import app as github_api_router
from openhands.server.routes.public import app as public_api_router
from openhands.server.routes.security import app as security_api_router
from openhands.server.shared import openhands_config

ATTACH_SESSION_MIDDLEWARE = import_from(openhands_config.ATTACH_SESSION_MIDDLEWARE_PATH)

app = FastAPI()
app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(NoCacheMiddleware)
app.add_middleware(
    RateLimitMiddleware, rate_limiter=InMemoryRateLimiter(requests=10, seconds=1)
)


@app.get('/health')
async def health():
    return 'OK'


app.include_router(public_api_router)
app.include_router(files_api_router)
app.include_router(conversation_api_router)
app.include_router(security_api_router)
app.include_router(feedback_api_router)
app.include_router(github_api_router)


app.middleware('http')(ATTACH_SESSION_MIDDLEWARE(app, target_router=files_api_router))
app.middleware('http')(
    ATTACH_SESSION_MIDDLEWARE(app, target_router=conversation_api_router)
)
app.middleware('http')(
    ATTACH_SESSION_MIDDLEWARE(app, target_router=security_api_router)
)
app.middleware('http')(
    ATTACH_SESSION_MIDDLEWARE(app, target_router=feedback_api_router)
)
