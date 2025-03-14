from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Optional

from database.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for public routes
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Get token from Authorization header
        authorization = request.headers.get("Authorization")
        token = None
        
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        
        # Verify token
        if token:
            payload = User.verify_token(token)
            if payload:
                # Attach user_id to request state
                request.state.user_id = payload.get("user_id")
                return await call_next(request)
        
        # If route requires authentication and no valid token, return 401
        if self._requires_auth(request.url.path):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # For routes that don't require auth, continue without user_id
        return await call_next(request)
    
    def _is_public_route(self, path: str) -> bool:
        """Check if route is public and doesn't need authentication"""
        public_routes = [
            "/api/auth/login",
            "/api/auth/register",
            "/health",
            "/api/public",
            "/assets",
        ]
        
        # Check if path starts with any public route
        return any(path.startswith(route) for route in public_routes)
    
    def _requires_auth(self, path: str) -> bool:
        """Check if route requires authentication"""
        # All API routes except public ones require authentication
        return path.startswith("/api/") and not self._is_public_route(path)

async def get_current_user_id(request: Request) -> Optional[int]:
    """Get current user ID from request state"""
    return getattr(request.state, "user_id", None)
