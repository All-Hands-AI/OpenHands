import os
import jwt
from typing import Dict

JWT_SECRET = os.getenv("JWT_SECRET", "5ecRe7")


def get_sid_from_token(token: str) -> str:
    """Gets the session id from a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload is None:
            print("Invalid token")
            return ""
        return payload["sid"]
    except Exception as e:
        print("Error decoding token:", e)
        return ""


def sign_token(payload: Dict[str, object]) -> str:
    """Signs a JWT token."""
    # payload = {
    #     "sid": sid,
    #     # "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    # }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
