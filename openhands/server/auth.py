import jwt
import requests
from jwt.exceptions import InvalidTokenError

from openhands.core.logger import openhands_logger as logger
from openhands.server.github_utils import GITHUB_APP_CLIENT_ID, GITHUB_APP_CLIENT_SECRET
from openhands.server.shared import config, file_store


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


def decode_gh_token(token: str, jwt_secret: str) -> tuple[str, str]:
    try:
        # Decode the JWT using the specified secret and algorithm
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])

        if 'access_token' in payload and 'refresh_token' in payload:
            return payload['access_token'], payload['refresh_token']
        else:
            logger.error('BOTH access_token and refresh_token not found in token')
            return '', ''
    except InvalidTokenError:
        logger.error('Invalid token')
    except Exception as e:
        logger.exception('Unexpected error decoding token: %s', e)
    return '', ''


def sign_token(payload: dict[str, object], jwt_secret: str) -> str:
    """Signs a JWT token."""
    # payload = {
    #     "sid": sid,
    #     # "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    # }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')


class TokenManager:
    GITHUB_API_URL = 'https://api.github.com'

    def __init__(self):
        self.file_store = file_store
        self.token_cred_path = '/tokens/{}/token.json'

    def store_tokens(self, access_token: str, refresh_token: str):
        token_path = sign_token({'access_token': access_token}, config.jwt_secret)
        token_cred_path = self.token_cred_path.format(token_path)

        signed_token = sign_token(
            {'access_token': access_token, 'refresh_token': refresh_token},
            config.jwt_secret,
        )
        self.file_store.write(token_cred_path, signed_token)

    def get_token(self, access_token: str) -> str:
        """Get refreshed access token"""

        signed_token = sign_token({'access_token': access_token}, config.jwt_secret)
        token_cred_file = self.token_cred_path.format(signed_token)

        try:
            cred = self.file_store.read(token_cred_file)
            _, refresh_token = decode_gh_token(cred, config.jwt_secret)
            self.file_store.delete(token_cred_file)
            new_token, new_refresh_token = self._refresh_token(refresh_token)
            self.store_tokens(new_token, new_refresh_token)
            return new_token
        except Exception as e:
            logger.warn(f'Exception occured at refresh {e}')
            return ''

    def _refresh_token(self, refresh_token):
        """
        Refresh the access token using GitHub's token refresh API.
        """
        url = 'https://github.com/login/oauth/access_token'

        # Prepare the payload
        payload = {
            'client_id': GITHUB_APP_CLIENT_ID,
            'client_secret': GITHUB_APP_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        # Make the POST request to refresh the token
        headers = {'Accept': 'application/json'}
        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')

            if not access_token or not refresh_token:
                raise ValueError(
                    'Failed to refresh token: missing access_token or refresh_token in response.'
                )

            return access_token, refresh_token
        else:
            # Handle errors
            error_message = response.json().get('error_description', response.text)
            raise Exception(f'Failed to refresh token: {error_message}')
