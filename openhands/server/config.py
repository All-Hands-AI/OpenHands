import os
import warnings
from dotenv import load_dotenv
from openhands.core.config import load_app_config
from openhands.storage import get_file_store
from openhands.server.session import SessionManager

load_dotenv()

config = load_app_config()
file_store = get_file_store(config.file_store, config.file_store_path)
session_manager = SessionManager(config, file_store)

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
