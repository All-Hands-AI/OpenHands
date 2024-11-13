import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
)

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.server.api.auth import app as auth_api_app
from openhands.server.api.public import app as public_api_app
from openhands.server.api.restricted import app as restricted_api_app
from openhands.server.middleware import LocalhostCORSMiddleware, NoCacheMiddleware
from openhands.server.static import app as static_app
from openhands.server.websocket import app as websocket_app

app = FastAPI()
app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.add_middleware(NoCacheMiddleware)

app.mount('/ws', websocket_app, name='ws')
app.mount('/api/options', public_api_app, name='public')
app.mount('/api', restricted_api_app, name='restricted')
app.mount('/', auth_api_app, name='auth')
app.mount('/', static_app, name='static')
