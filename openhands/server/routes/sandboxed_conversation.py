"""Router for sandboxed conversation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.server.session.sandboxed_conversation_service_resolver import (
    SandboxedConversationServiceResolver,
)
from openhands.storage.files import FileStore
from openhands.storage.memory import InMemoryFileStore

router = APIRouter(
    prefix='/api/sandboxed-conversations', tags=['sandboxed-conversations']
)


class CreateSandboxedConversationRequest(BaseModel):
    """Request model for creating a sandboxed conversation."""

    sid: str
    user_id: str | None = None


class SandboxedConversationResponse(BaseModel):
    """Response model for sandboxed conversation operations."""

    sid: str
    user_id: str | None
    is_connected: bool
    working_directory: str | None = None


def get_config() -> OpenHandsConfig:
    """Dependency to get OpenHands configuration."""
    return OpenHandsConfig()


def get_file_store(config: OpenHandsConfig = Depends(get_config)) -> FileStore:
    """Dependency to get file store."""
    return InMemoryFileStore()


@router.post('/create', response_model=SandboxedConversationResponse)
async def create_sandboxed_conversation(
    request: CreateSandboxedConversationRequest,
    config: OpenHandsConfig = Depends(get_config),
    file_store: FileStore = Depends(get_file_store),
):
    """Create a new sandboxed conversation using secured resolver.

    This endpoint demonstrates external usage that should use the secured resolver.
    """
    try:
        logger.info(f'Creating sandboxed conversation for session {request.sid}')

        # Use secured resolver for external API access
        resolver = SandboxedConversationServiceResolver.get_resolver_for_user(
            user_id=request.user_id,
            config=config,
            file_store=file_store,
        )

        # Create the service through the resolver
        service = resolver.resolve(sid=request.sid, user_id=request.user_id)

        # Connect to the sandboxed environment
        await service.connect()

        # Get working directory if available
        working_directory = None
        try:
            working_directory = service.get_working_directory()
        except Exception as e:
            logger.warning(f'Could not get working directory: {e}')

        return SandboxedConversationResponse(
            sid=request.sid,
            user_id=request.user_id,
            is_connected=service.is_connected(),
            working_directory=working_directory,
        )

    except Exception as e:
        logger.error(f'Failed to create sandboxed conversation: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{sid}/status', response_model=SandboxedConversationResponse)
async def get_sandboxed_conversation_status(
    sid: str,
    user_id: str | None = None,
    config: OpenHandsConfig = Depends(get_config),
    file_store: FileStore = Depends(get_file_store),
):
    """Get the status of a sandboxed conversation using secured resolver.

    This endpoint demonstrates external usage that should use the secured resolver.
    """
    try:
        logger.info(f'Getting status for sandboxed conversation {sid}')

        # Use secured resolver for external API access
        resolver = SandboxedConversationServiceResolver.get_resolver_for_user(
            user_id=user_id,
            config=config,
            file_store=file_store,
        )

        # Create the service through the resolver (this would typically be retrieved from storage)
        service = resolver.resolve(sid=sid, user_id=user_id)

        # Get working directory if available
        working_directory = None
        try:
            working_directory = service.get_working_directory()
        except Exception as e:
            logger.warning(f'Could not get working directory: {e}')

        return SandboxedConversationResponse(
            sid=sid,
            user_id=user_id,
            is_connected=service.is_connected(),
            working_directory=working_directory,
        )

    except Exception as e:
        logger.error(f'Failed to get sandboxed conversation status: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{sid}')
async def cleanup_sandboxed_conversation(
    sid: str,
    user_id: str | None = None,
    config: OpenHandsConfig = Depends(get_config),
    file_store: FileStore = Depends(get_file_store),
):
    """Cleanup a sandboxed conversation using secured resolver.

    This endpoint demonstrates external usage that should use the secured resolver.
    """
    try:
        logger.info(f'Cleaning up sandboxed conversation {sid}')

        # Use secured resolver for external API access
        resolver = SandboxedConversationServiceResolver.get_resolver_for_user(
            user_id=user_id,
            config=config,
            file_store=file_store,
        )

        # Create the service through the resolver (this would typically be retrieved from storage)
        service = resolver.resolve(sid=sid, user_id=user_id)

        # Disconnect from the sandboxed environment
        await service.disconnect()

        return {'message': f'Sandboxed conversation {sid} cleaned up successfully'}

    except Exception as e:
        logger.error(f'Failed to cleanup sandboxed conversation: {e}')
        raise HTTPException(status_code=500, detail=str(e))
