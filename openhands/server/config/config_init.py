from openhands.core.config.utils import load_app_config
from openhands.server.config.server_config import load_server_config
from openhands.storage import get_file_store

config = load_app_config()
server_config = load_server_config()
file_store = get_file_store(config.file_store, config.file_store_path)
