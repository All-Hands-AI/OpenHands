import jwt
from jwt.exceptions import InvalidTokenError

from openhands.core.logger import openhands_logger as logger


def get_sid_from_token(token: str, jwt_secret: str) -> str:
    """Retrieve the session ID from a JWT token.

    This function decodes and validates a JWT token, extracting the session ID
    if present and valid. It performs several validation steps:
    1. Validates the token signature using the secret
    2. Verifies the payload is a dictionary
    3. Checks for the presence of 'sid' in the payload
    4. Validates that the sid is a string

    Args:
        token: The JWT token to decode
        jwt_secret: Secret key used to verify the token signature

    Returns:
        str: The session ID if found and valid, otherwise an empty string

    Notes:
        - Returns empty string for any validation failure
        - Logs specific error messages for different failure cases
        - Does not raise exceptions, but handles them internally
    """
    # Input validation
    if not token or not isinstance(token, str):
        logger.error('Invalid token format: token must be a non-empty string')
        return ''
        
    if not jwt_secret or not isinstance(jwt_secret, str):
        logger.error('Invalid JWT secret: secret must be a non-empty string')
        return ''
    try:
        # Decode the JWT using the specified secret and algorithm
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])

        # Ensure the payload contains 'sid'
        if not isinstance(payload, dict):
            logger.error('Token payload is not a dictionary')
            return ''
            
        if 'sid' not in payload:
            logger.error('SID not found in token payload')
            return ''
            
        sid = payload['sid']
        if not isinstance(sid, str):
            logger.error('SID in token is not a string')
            return ''
            
        return sid
    except InvalidTokenError as e:
        # More specific error for invalid tokens
        logger.error(f'Invalid token format or signature: {str(e)}')
    except (TypeError, ValueError) as e:
        # Handle type/value errors from jwt.decode
        logger.error(f'Error decoding token data: {str(e)}')
    return ''


def sign_token(payload: dict[str, object], jwt_secret: str) -> str:
    """Signs a JWT token.
    
    Args:
        payload: Dictionary containing the data to encode in the token
        jwt_secret: Secret key used to sign the token
        
    Returns:
        str: The signed JWT token
        
    Raises:
        TypeError: If payload is not a dictionary or contains invalid types
        ValueError: If jwt_secret is empty or invalid
    """
    if not isinstance(payload, dict):
        raise TypeError('Payload must be a dictionary')
        
    if not jwt_secret:
        raise ValueError('JWT secret cannot be empty')
        
    try:
        return jwt.encode(payload, jwt_secret, algorithm='HS256')
    except (TypeError, ValueError) as e:
        logger.error(f'Error encoding JWT token: {str(e)}')
        raise
