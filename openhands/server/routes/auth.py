from datetime import datetime, timedelta
import os
from typing import Optional
from eth_account.messages import encode_defunct
from web3 import Web3
import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from openhands.server.db import database
from openhands.server.models import User
from fastapi import APIRouter
from openhands.core.logger import openhands_logger as logger
from openhands.server.utils.crypto import generate_mnemonic

app = APIRouter(prefix='/api/auth')

# Message that users will sign with their wallet
AUTH_MESSAGE = "Sign this message to authenticate with OpenHands"
# JWT settings
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')  # In production, this should be in environment variables
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_IN = None  # Token never expires

class SignupRequest(BaseModel):
    publicAddress: str
    signature: str

class SignupResponse(BaseModel):
    token: str
    user: dict

def create_jwt_token(user_id: str) -> str:
    """Create a JWT token for the user."""
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
    }
    if JWT_EXPIRES_IN:
        payload["exp"] = datetime.utcnow() + timedelta(seconds=JWT_EXPIRES_IN)
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_ethereum_signature(public_address: str, signature: str) -> bool:
    """Verify that the signature was signed by the public address."""
    try:
        w3 = Web3()
        message = encode_defunct(text=AUTH_MESSAGE)
        recovered_address = w3.eth.account.recover_message(message, signature=signature)
        return recovered_address.lower() == public_address.lower()
    except Exception:
        return False

@app.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest) -> SignupResponse:
    """Sign up with Ethereum wallet."""
    # Verify the signature
    if not verify_ethereum_signature(request.publicAddress, request.signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Check if user already exists
    query = select(User).where(User.c.public_key == request.publicAddress.lower())
    existing_user = await database.fetch_one(query)
    if existing_user:
        # If user exists, just return a new token
        token = create_jwt_token(existing_user["public_key"])
        return SignupResponse(
            token=token,
            user={
                "id": existing_user["public_key"],
                "publicAddress": existing_user["public_key"]
            }
        )
    
    user_data = {
        "public_key": request.publicAddress.lower(),
        "mnemonic": generate_mnemonic(),
        "jwt": create_jwt_token(request.publicAddress.lower())
    }
    
    await database.execute(User.insert().values(user_data))
    
    return SignupResponse(
        token=user_data["jwt"],
        user={
            "id": user_data["public_key"],
            "publicAddress": user_data["public_key"]
        }
    ) 