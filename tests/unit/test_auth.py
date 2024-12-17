from unittest import TestCase

from openhands.server.auth import AuthError, decrypt_str, encrypt_str


class TestAuth(TestCase):
    def test_round_trip(self):
        message = 'some message to encrypt'
        jwt_secret = 'some secret value'
        encrypted = encrypt_str(message, jwt_secret)
        decrypted = decrypt_str(encrypted, jwt_secret)
        assert decrypted == message

    def test_emoji(self):
        # Verify that non ascii / English charaters work as expected
        message = '😊'
        jwt_secret = '👿'
        encrypted = encrypt_str(message, jwt_secret)
        decrypted = decrypt_str(encrypted, jwt_secret)
        assert decrypted == message

    def test_blank(self):
        message = ''
        jwt_secret = 'some secret value'
        encrypted = encrypt_str(message, jwt_secret)
        decrypted = decrypt_str(encrypted, jwt_secret)
        assert decrypted == message

    def test_invalid(self):
        value = 'not encrypted'
        jwt_secret = 'some secret value'
        with self.assertRaises(AuthError):
            decrypt_str(value, jwt_secret)
