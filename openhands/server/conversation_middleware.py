from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable

from openhands.server import shared
from openhands.server.types import SessionMiddlewareInterface


class AttachConversationMiddleware(SessionMiddlewareInterface):
    def __init__(self, app):
        self.app = app

    def _should_attach(self, request) -> bool:
        """
        Determine if the middleware should attach a session for the given request.
        """
        if request.method == 'OPTIONS':
            return False

        conversation_id = ''
        if request.url.path.startswith('/api/conversation'):
            # FIXME: we should be able to use path_params
            path_parts = request.url.path.split('/')
            if len(path_parts) > 4:
                conversation_id = request.url.path.split('/')[3]
        if not conversation_id:
            return False

        request.state.sid = conversation_id

        return True

    async def _attach_conversation(self, request: Request) -> JSONResponse | None:
        """
        Attach the user's session based on the provided authentication token.
        """
        request.state.conversation = (
            await shared.conversation_manager.attach_to_conversation(request.state.sid)
        )
        if not request.state.conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Session not found'},
            )
        return None

    async def _detach_session(self, request: Request) -> None:
        """
        Detach the user's session.
        """
        await shared.conversation_manager.detach_from_conversation(
            request.state.conversation
        )

    async def __call__(self, request: Request, call_next: Callable):
        if not self._should_attach(request):
            return await call_next(request)

        response = await self._attach_conversation(request)
        if response:
            return response

        try:
            # Continue processing the request
            response = await call_next(request)
        finally:
            # Ensure the session is detached
            await self._detach_session(request)

        return response