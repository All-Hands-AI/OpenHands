from uuid import uuid4

from openhands.storage import get_file_store

JWT_SECRET = '.jwt_secret'


def get_or_create_jwt_secret(file_store_type: str, file_store_path: str) -> str:
    file_store = get_file_store(file_store_type, file_store_path)
    try:
        jwt_secret = file_store.read(JWT_SECRET)
        return jwt_secret
    except FileNotFoundError:
        new_secret = uuid4().hex
        file_store.write(JWT_SECRET, new_secret)
        return new_secret
