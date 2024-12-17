import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode

import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jwt.exceptions import InvalidTokenError

from openhands.core.logger import openhands_logger as logger

backend = default_backend()
iterations = 100_000


class AuthError(Exception):
    """Exception raised when there was an authenticatione error"""

    def __init__(self, error: str):
        self.error = error

    def __str__(self):
        return self.error


def get_sid_from_token(token: str, jwt_secret: str) -> str:
    """Retrieves the session id from a JWT token.

    Parameters:
        token (str): The JWT token from which the session id is to be extracted.

    Returns:
        str: The session id if found and valid, otherwise an empty string.
    """
    try:
        # Decode the JWT using the specified secret and algorithm
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])

        # Ensure the payload contains 'sid'
        if 'sid' in payload:
            return payload['sid']
        else:
            logger.error('SID not found in token')
            return ''
    except InvalidTokenError:
        logger.error('Invalid token')
    except Exception as e:
        logger.exception('Unexpected error decoding token: %s', e)
    return ''


def sign_token(payload: dict[str, object], jwt_secret: str, algorithm='HS256') -> str:
    """Signs a JWT token."""
    # payload = {
    #     "sid": sid,
    #     # "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    # }
    return jwt.encode(payload, jwt_secret, algorithm=algorithm)


def _derive_key(password: bytes, salt: bytes, iterations: int = iterations) -> bytes:
    """Derive a secret key from a given password and salt"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=backend,
    )
    return urlsafe_b64encode(kdf.derive(password))


def encrypt_str(message: str, jwt_secret: str) -> str:
    salt = secrets.token_bytes(16)
    key = _derive_key(jwt_secret.encode(), salt, iterations)
    encrypted = urlsafe_b64encode(
        b'%b%b%b'
        % (
            salt,
            iterations.to_bytes(4, 'big'),
            urlsafe_b64decode(Fernet(key).encrypt(message.encode())),
        )
    )
    return encrypted.decode()


def decrypt_str(message: str, jwt_secret: str) -> str:
    try:
        decoded = urlsafe_b64decode(message)
        salt, iter, token = (
            decoded[:16],
            decoded[16:20],
            urlsafe_b64encode(decoded[20:]),
        )
        iterations = int.from_bytes(iter, 'big')
        key = _derive_key(jwt_secret.encode(), salt, iterations)
        decrypted = Fernet(key).decrypt(token)
        return decrypted.decode()
    except:  # noqa: E722
        # Fernet throws rust implementation throws a PanicException which does not extend python's Exception
        # So we don't catch a specific type here.
        raise AuthError('error_decrypting')
