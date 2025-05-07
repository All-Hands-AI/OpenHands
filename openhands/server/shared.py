import os
from functools import lru_cache

import socketio
from dotenv import load_dotenv

from openhands.core.config import load_app_config
from openhands.server.config.server_config import load_server_config
from openhands.server.conversation_manager.conversation_manager import (
    ConversationManager,
)
from openhands.server.monitoring import MonitoringListener
from openhands.server.utils.s3_utils import S3Handler
from openhands.storage import get_file_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

load_dotenv()

config = load_app_config()
server_config = load_server_config()
file_store = get_file_store(config.file_store, config.file_store_path)

client_manager = None
# redis_host = os.environ.get('REDIS_HOST')
# if redis_host:
#     client_manager = socketio.AsyncRedisManager(
#         f'redis://{redis_host}',
#         redis_options={'password': os.environ.get('REDIS_PASSWORD')},
#     )


sio = socketio.AsyncServer(
    async_mode='asgi', cors_allowed_origins='*', client_manager=client_manager
)

MonitoringListenerImpl = get_impl(
    MonitoringListener,
    server_config.monitoring_listener_class,
)

monitoring_listener = MonitoringListenerImpl.get_instance(config)

ConversationManagerImpl = get_impl(
    ConversationManager,  # type: ignore
    server_config.conversation_manager_class,
)

conversation_manager: ConversationManager = ConversationManagerImpl.get_instance(  # type: ignore
    sio, config, file_store, server_config, monitoring_listener
)

SettingsStoreImpl: SettingsStore = get_impl(
    SettingsStore, server_config.settings_store_class
)  # type: ignore

ConversationStoreImpl: ConversationStore = get_impl(
    ConversationStore,  # type: ignore
    server_config.conversation_store_class,
)


@lru_cache
def get_s3_handler():
    if (
        not os.getenv('S3_ACCESS_KEY_ID')
        or not os.getenv('S3_SECRET_ACCESS_KEY')
        or not os.getenv('S3_BUCKET')
    ):
        return None
    return S3Handler()


s3_handler = get_s3_handler()
