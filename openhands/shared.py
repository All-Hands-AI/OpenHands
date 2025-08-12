import hashlib

from openhands.core.config import load_app_config

config = load_app_config()


def get_hash(text: str):
    hash_digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return hash_digest
