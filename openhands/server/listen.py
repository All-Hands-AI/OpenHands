import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
)

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.server.middleware import LocalhostCORSMiddleware, NoCacheMiddleware
from openhands.server.routes.auth import app as auth_api_router
from openhands.server.routes.public import app as public_api_router
from openhands.server.routes.restricted import AttachSessionMiddleware
from openhands.server.routes.restricted import app as restricted_api_router
from openhands.server.routes.websocket import app as websocket_router
from openhands.server.static import SPAStaticFiles

app = FastAPI()
app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.add_middleware(NoCacheMiddleware)

app.include_router(auth_api_router)
app.include_router(public_api_router)
app.include_router(restricted_api_router)
app.include_router(websocket_router)

app.middleware('http')(
    AttachSessionMiddleware(app, target_router=restricted_api_router)
)

app.mount('/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist')
