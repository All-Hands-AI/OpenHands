from urllib.parse import urlparse

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


from typing import Optional

from openhands.core.logger import openhands_logger as logger


class LocalhostCORSMiddleware(CORSMiddleware):
    """Custom CORS middleware for local development.
    
    This middleware extends the standard CORS middleware to allow any request from
    localhost/127.0.0.1 domains, while maintaining standard CORS rules for other
    origins. This is useful for local development where different ports might be used.
    
    Attributes:
        app: The ASGI application
        allow_origins: List of allowed origins from parent class
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers
        allow_credentials: Whether to allow credentials
    """

    def __init__(self, app: ASGIApp, **kwargs) -> None:
        """Initialize the middleware.
        
        Args:
            app: The ASGI application
            **kwargs: Additional arguments passed to CORSMiddleware
        """
        try:
            super().__init__(app, **kwargs)
            logger.debug('Initialized LocalhostCORSMiddleware')
        except Exception as e:
            logger.error(f'Failed to initialize CORS middleware: {str(e)}')
            raise

    def is_allowed_origin(self, origin: Optional[str]) -> bool:
        """Check if an origin is allowed.
        
        This method extends the standard CORS origin check to always allow
        localhost and 127.0.0.1 origins, regardless of port number.
        
        Args:
            origin: The origin to check, may be None
            
        Returns:
            bool: True if the origin is allowed, False otherwise
            
        Notes:
            - Always returns True for localhost/127.0.0.1
            - Falls back to parent class logic for other origins
            - Handles None origin gracefully
        """
        try:
            # Handle None origin
            if not origin:
                logger.debug('No origin provided in request')
                return super().is_allowed_origin(origin)
                
            # Parse origin URL
            try:
                parsed = urlparse(origin)
                hostname = parsed.hostname or ''
            except Exception as e:
                logger.warning(f'Failed to parse origin URL {origin}: {str(e)}')
                return False
                
            # Check for localhost
            if hostname in ['localhost', '127.0.0.1']:
                logger.debug(f'Allowing localhost origin: {origin}')
                return True
                
            # Use parent class logic for other origins
            is_allowed = super().is_allowed_origin(origin)
            if is_allowed:
                logger.debug(f'Origin allowed by parent rules: {origin}')
            else:
                logger.debug(f'Origin blocked by parent rules: {origin}')
            return is_allowed
            
        except Exception as e:
            logger.error(f'Error checking origin {origin}: {str(e)}')
            return False  # Fail safe by blocking request


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Middleware to control caching behavior.
    
    This middleware disables caching for all routes except static assets by adding
    appropriate cache control headers to responses. This ensures that dynamic content
    is always fresh while allowing static assets to be cached.
    
    The following headers are set for non-asset routes:
    - Cache-Control: no-cache, no-store, must-revalidate, max-age=0
    - Pragma: no-cache
    - Expires: 0
    
    Notes:
        - Routes starting with /assets are excluded from cache control
        - Headers are added even if the response already has cache headers
        - Any error in header setting is logged but doesn't fail the request
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        logger.debug('Initialized NoCacheMiddleware')

    async def dispatch(self, request, call_next):
        """Process a request and modify cache headers.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint to call
            
        Returns:
            Response: The response with modified cache headers
            
        Notes:
            - Any error in the wrapped endpoint is propagated
            - Header modification errors are caught and logged
        """
        try:
            # Get request ID for logging
            request_id = getattr(request.state, 'request_id', id(request))
            logger.debug(f'Processing request {request_id} in NoCacheMiddleware')
            
            # Process request
            response = await call_next(request)
            
            # Skip assets
            if request.url.path.startswith('/assets'):
                logger.debug(f'Skipping cache control for asset: {request.url.path}')
                return response
                
            # Add cache control headers
            try:
                response.headers['Cache-Control'] = (
                    'no-cache, no-store, must-revalidate, max-age=0'
                )
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                logger.debug(f'Added cache control headers for {request.url.path}')
            except Exception as e:
                logger.error(
                    f'Failed to set cache headers for {request.url.path}: {str(e)}'
                )
                
            return response
            
        except Exception as e:
            logger.error(f'Error in cache middleware: {str(e)}', exc_info=True)
            raise  # Re-raise to be handled by error middleware
