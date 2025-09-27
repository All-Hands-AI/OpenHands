"""Internal service for managing sandboxed conversations."""

from typing import Any

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.server.session.sandboxed_conversation_service import (
    SandboxedConversationService,
)
from openhands.server.session.sandboxed_conversation_service_resolver import (
    SandboxedConversationServiceResolver,
)
from openhands.storage.files import FileStore


class InternalSandboxedConversationService:
    """Internal service for managing sandboxed conversations.

    This service demonstrates internal usage that can use the unsecured resolver
    for system-level operations.
    """

    def __init__(self, config: OpenHandsConfig, file_store: FileStore):
        """Initialize the internal service.

        Args:
            config: OpenHands configuration
            file_store: File storage instance
        """
        self.config = config
        self.file_store = file_store
        self._active_conversations: dict[str, SandboxedConversationService] = {}

    async def create_system_conversation(
        self, sid: str
    ) -> SandboxedConversationService:
        """Create a system-level sandboxed conversation.

        This method uses the unsecured resolver since it's for internal system operations.

        Args:
            sid: Session ID for the conversation

        Returns:
            A SandboxedConversationService instance
        """
        logger.info(f'Creating system sandboxed conversation for session {sid}')

        # Use unsecured resolver for internal system operations
        resolver = SandboxedConversationServiceResolver.get_unsecured_resolver(
            config=self.config,
            file_store=self.file_store,
        )

        # Create the service through the resolver
        service = resolver.resolve(
            sid=sid, user_id=None
        )  # No user_id for system conversations

        # Connect to the sandboxed environment
        await service.connect()

        # Store the active conversation
        self._active_conversations[sid] = service

        return service

    async def cleanup_system_conversation(self, sid: str) -> bool:
        """Cleanup a system-level sandboxed conversation.

        Args:
            sid: Session ID for the conversation

        Returns:
            True if cleanup was successful, False otherwise
        """
        logger.info(f'Cleaning up system sandboxed conversation for session {sid}')

        if sid not in self._active_conversations:
            logger.warning(f'No active conversation found for session {sid}')
            return False

        try:
            service = self._active_conversations[sid]
            await service.disconnect()
            del self._active_conversations[sid]
            return True
        except Exception as e:
            logger.error(f'Failed to cleanup system conversation {sid}: {e}')
            return False

    async def get_active_conversations(self) -> list[str]:
        """Get list of active conversation session IDs.

        Returns:
            List of active session IDs
        """
        return list(self._active_conversations.keys())

    async def get_conversation_status(self, sid: str) -> dict[str, Any]:
        """Get status information for a conversation.

        Args:
            sid: Session ID for the conversation

        Returns:
            Dictionary containing status information
        """
        if sid not in self._active_conversations:
            return {'exists': False}

        service = self._active_conversations[sid]

        try:
            working_directory = service.get_working_directory()
        except Exception:
            working_directory = None

        return {
            'exists': True,
            'is_connected': service.is_connected(),
            'working_directory': working_directory,
            'user_id': service.user_id,
        }

    async def cleanup_all_conversations(self) -> int:
        """Cleanup all active conversations.

        Returns:
            Number of conversations cleaned up
        """
        logger.info('Cleaning up all system sandboxed conversations')

        cleanup_count = 0
        for sid in list(self._active_conversations.keys()):
            if await self.cleanup_system_conversation(sid):
                cleanup_count += 1

        return cleanup_count

    async def perform_maintenance(self) -> dict[str, Any]:
        """Perform maintenance operations on active conversations.

        This method demonstrates internal operations that might need
        to access conversations without user context.

        Returns:
            Dictionary containing maintenance results
        """
        logger.info('Performing maintenance on sandboxed conversations')

        maintenance_results = {
            'total_conversations': len(self._active_conversations),
            'healthy_conversations': 0,
            'unhealthy_conversations': 0,
            'cleaned_up_conversations': 0,
        }

        # Check health of all conversations
        unhealthy_sids = []
        for sid, service in self._active_conversations.items():
            try:
                if service.is_connected():
                    maintenance_results['healthy_conversations'] += 1
                else:
                    maintenance_results['unhealthy_conversations'] += 1
                    unhealthy_sids.append(sid)
            except Exception as e:
                logger.warning(f'Error checking health of conversation {sid}: {e}')
                maintenance_results['unhealthy_conversations'] += 1
                unhealthy_sids.append(sid)

        # Cleanup unhealthy conversations
        for sid in unhealthy_sids:
            if await self.cleanup_system_conversation(sid):
                maintenance_results['cleaned_up_conversations'] += 1

        return maintenance_results
