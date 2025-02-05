from dotenv import load_dotenv

from openhands.core.config import load_app_config
from openhands.server.config.server_config import load_server_config
from openhands.storage import get_file_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

load_dotenv()

config = load_app_config()
server_config = load_server_config()
file_store = get_file_store(config.file_store, config.file_store_path)

ConversationStoreImpl = get_impl(
    ConversationStore,  # type: ignore
    server_config.conversation_store_class,
)

SettingsStoreImpl = get_impl(SettingsStore, server_config.settings_store_class)  # type: ignore
