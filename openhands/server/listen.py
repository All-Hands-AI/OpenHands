import socketio

from openhands.server.app import app as base_app
from openhands.server.listen_socket import sio
from openhands.server.middleware import (
    AttachConversationMiddleware,
    CacheControlMiddleware,
    GitHubTokenMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
)
from openhands.server.shared import server_config
from openhands.server.static import SPAStaticFiles
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

base_app.mount(
    '/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist'
)

SettingsStoreImpl = get_impl(SettingsStore, server_config.settings_store_class)  # type: ignore

base_app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

base_app.add_middleware(CacheControlMiddleware)
base_app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=InMemoryRateLimiter(requests=10, seconds=1),
)
base_app.middleware('http')(AttachConversationMiddleware(base_app))
base_app.middleware('http')(GitHubTokenMiddleware(base_app, SettingsStoreImpl))  # type: ignore

app = socketio.ASGIApp(sio, other_asgi_app=base_app)
