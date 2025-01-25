import os

import socketio
from dotenv import load_dotenv

from openhands.core.config import load_app_config
from openhands.server.config.openhands_config import load_openhands_config
from openhands.server.conversation_manager.conversation_manager import (
    ConversationManager,
)
from openhands.storage import get_file_store
from openhands.utils.import_utils import get_impl

load_dotenv()

config = load_app_config()
openhands_config = load_openhands_config()
file_store = get_file_store(config.file_store, config.file_store_path)

from openhands.storage.docker_snapshots import sudo_command
if config.sandbox.docker_snapshots:
    sudo_command(["enable"])
else:
    sudo_command(["disable"])

client_manager = None
redis_host = os.environ.get('REDIS_HOST')
if redis_host:
    client_manager = socketio.AsyncRedisManager(
        f'redis://{redis_host}',
        redis_options={'password': os.environ.get('REDIS_PASSWORD')},
    )


sio = socketio.AsyncServer(
    async_mode='asgi', cors_allowed_origins='*', client_manager=client_manager
)

ConversationManagerImpl = get_impl(
    ConversationManager,  # type: ignore
    openhands_config.conversation_manager_class,
)
conversation_manager = ConversationManagerImpl.get_instance(sio, config, file_store)
