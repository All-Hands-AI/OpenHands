"""Resolver for SandboxedConversationService with secured and unsecured access patterns."""

from abc import ABC, abstractmethod

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStream
from openhands.runtime.base import Runtime
from openhands.server.session.sandboxed_conversation_service import (
    SandboxedConversationService,
)
from openhands.storage.files import FileStore


class SandboxedConversationServiceResolver(ABC):
    """Abstract base class for resolving SandboxedConversationService instances."""

    def __init__(
        self,
        config: OpenHandsConfig,
        file_store: FileStore,
    ):
        """Initialize the resolver.

        Args:
            config: OpenHands configuration
            file_store: File storage instance
        """
        self.config = config
        self.file_store = file_store

    @abstractmethod
    def resolve(
        self,
        sid: str,
        user_id: str | None = None,
        event_stream: EventStream | None = None,
        runtime: Runtime | None = None,
    ) -> SandboxedConversationService:
        """Resolve a SandboxedConversationService instance.

        Args:
            sid: Session ID for the conversation
            user_id: User ID associated with the conversation
            event_stream: Optional event stream
            runtime: Optional runtime instance

        Returns:
            A SandboxedConversationService instance
        """
        pass

    @classmethod
    def get_resolver_for_user(
        cls,
        user_id: str | None,
        config: OpenHandsConfig,
        file_store: FileStore,
    ) -> 'SandboxedConversationServiceResolver':
        """Get a secured resolver for a specific user.

        Args:
            user_id: The user ID to create a secured resolver for
            config: OpenHands configuration
            file_store: File storage instance

        Returns:
            A secured resolver instance
        """
        logger.warning(
            'Secured SandboxedConversationServiceResolver requested but not yet implemented. '
            'Returning unsecured resolver for now.'
        )
        return cls.get_unsecured_resolver(config, file_store)

    @classmethod
    def get_unsecured_resolver(
        cls,
        config: OpenHandsConfig,
        file_store: FileStore,
    ) -> 'SandboxedConversationServiceResolver':
        """Get an unsecured resolver.

        Args:
            config: OpenHands configuration
            file_store: File storage instance

        Returns:
            An unsecured resolver instance
        """
        return UnsecuredSandboxedConversationServiceResolver(config, file_store)


class UnsecuredSandboxedConversationServiceResolver(
    SandboxedConversationServiceResolver
):
    """Unsecured implementation of SandboxedConversationServiceResolver."""

    def resolve(
        self,
        sid: str,
        user_id: str | None = None,
        event_stream: EventStream | None = None,
        runtime: Runtime | None = None,
    ) -> SandboxedConversationService:
        """Resolve a SandboxedConversationService instance without security restrictions.

        Args:
            sid: Session ID for the conversation
            user_id: User ID associated with the conversation
            event_stream: Optional event stream
            runtime: Optional runtime instance

        Returns:
            A SandboxedConversationService instance
        """
        logger.debug(
            f'Resolving unsecured SandboxedConversationService for session {sid}'
        )

        return SandboxedConversationService(
            sid=sid,
            file_store=self.file_store,
            config=self.config,
            user_id=user_id,
            event_stream=event_stream,
            runtime=runtime,
        )


class SecuredSandboxedConversationServiceResolver(SandboxedConversationServiceResolver):
    """Secured implementation of SandboxedConversationServiceResolver (placeholder for future implementation)."""

    def __init__(
        self,
        config: OpenHandsConfig,
        file_store: FileStore,
        user_id: str | None,
    ):
        """Initialize the secured resolver.

        Args:
            config: OpenHands configuration
            file_store: File storage instance
            user_id: User ID for security context
        """
        super().__init__(config, file_store)
        self.user_id = user_id

    def resolve(
        self,
        sid: str,
        user_id: str | None = None,
        event_stream: EventStream | None = None,
        runtime: Runtime | None = None,
    ) -> SandboxedConversationService:
        """Resolve a SandboxedConversationService instance with security restrictions.

        Args:
            sid: Session ID for the conversation
            user_id: User ID associated with the conversation
            event_stream: Optional event stream
            runtime: Optional runtime instance

        Returns:
            A SandboxedConversationService instance
        """
        # For now, this is a placeholder that behaves like the unsecured resolver
        # In the future, this would implement proper security checks and isolation
        logger.debug(
            f'Resolving secured SandboxedConversationService for session {sid} and user {self.user_id}'
        )

        # Validate that the user_id matches the resolver's user_id for security
        if user_id is not None and user_id != self.user_id:
            logger.warning(
                f'User ID mismatch in secured resolver: expected {self.user_id}, got {user_id}'
            )

        return SandboxedConversationService(
            sid=sid,
            file_store=self.file_store,
            config=self.config,
            user_id=self.user_id,  # Use the resolver's user_id for security
            event_stream=event_stream,
            runtime=runtime,
        )
