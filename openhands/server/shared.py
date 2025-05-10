import os

import socketio
from dotenv import load_dotenv

from openhands.core.config import load_app_config
from openhands.server.config.server_config import ServerConfig, load_server_config
from openhands.server.conversation_manager.conversation_manager import (
    ConversationManager,
)
from openhands.server.monitoring import MonitoringListener
from openhands.storage import get_file_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

load_dotenv()

config = load_app_config()
server_config = load_server_config()
file_store = get_file_store(config.file_store, config.file_store_path)

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

monitoring_class = (
    getattr(server_config, 'monitoring_listener_class', None)
    if isinstance(server_config, ServerConfig)
    else None
)
MonitoringListenerImpl = get_impl(
    MonitoringListener,
    monitoring_class,
)

monitoring_listener = MonitoringListenerImpl.get_instance(config)

conversation_manager_class = (
    getattr(server_config, 'conversation_manager_class', None)
    if isinstance(server_config, ServerConfig)
    else None
)
ConversationManagerImpl = get_impl(
    ConversationManager,
    conversation_manager_class,
)

conversation_manager = ConversationManagerImpl.get_instance(
    sio, config, file_store, server_config, monitoring_listener
)

settings_store_class = (
    getattr(server_config, 'settings_store_class', None)
    if isinstance(server_config, ServerConfig)
    else None
)
SettingsStoreImpl = get_impl(SettingsStore, settings_store_class)

secret_store_class = (
    getattr(server_config, 'secret_store_class', None)
    if isinstance(server_config, ServerConfig)
    else None
)
SecretsStoreImpl = get_impl(SecretsStore, secret_store_class)

conversation_store_class = (
    getattr(server_config, 'conversation_store_class', None)
    if isinstance(server_config, ServerConfig)
    else None
)
ConversationStoreImpl = get_impl(ConversationStore, conversation_store_class)
