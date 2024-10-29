from urllib.parse import urlparse

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class CustomCORSMiddleware(CORSMiddleware):
    """
    Custom CORS middleware that allows CORS requests from any origin where the domain is localhost
    (Allowing any port)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(
            app=app,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    def is_allowed_origin(self, origin: str) -> bool:
        domain = urlparse(origin).netloc.split(':')[0]
        if domain in ('localhost', '127.0.0.1'):
            return True
        return super().is_allowed_origin(origin)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to disable caching for all routes by adding appropriate headers
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith('/assets'):
            response.headers['Cache-Control'] = (
                'no-cache, no-store, must-revalidate, max-age=0'
            )
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
