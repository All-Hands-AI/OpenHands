import os

import socketio

from openhands.server.config.config_init import config, file_store, server_config
from openhands.server.conversation_manager.conversation_manager import (
    ConversationManager,
)
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

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
    server_config.conversation_manager_class,
)
conversation_manager = ConversationManagerImpl.get_instance(sio, config, file_store)

SettingsStoreImpl = get_impl(SettingsStore, server_config.settings_store_class)  # type: ignore

ConversationStoreImpl = get_impl(
    ConversationStore,  # type: ignore
    server_config.conversation_store_class,
)
