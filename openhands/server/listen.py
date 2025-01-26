import socketio

from openhands.server.app import app as base_app
from openhands.server.listen_socket import sio
from openhands.server.static import SPAStaticFiles

base_app.mount(
    '/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist'
)

app = socketio.ASGIApp(sio, other_asgi_app=base_app)
