"""Example usage of SandboxedConversationService with resolver pattern."""

from openhands.core.config import OpenHandsConfig
from openhands.server.session.sandboxed_conversation_service import (
    SandboxedConversationService,
)
from openhands.server.session.sandboxed_conversation_service_resolver import (
    SandboxedConversationServiceResolver,
)
from openhands.storage.memory import InMemoryFileStore


async def create_sandboxed_conversation_secured(sid: str, user_id: str | None = None):
    """Example function showing how to create a sandboxed conversation using secured resolver."""
    config = OpenHandsConfig()
    file_store = InMemoryFileStore()

    # Use secured resolver (recommended for external usage)
    resolver = SandboxedConversationServiceResolver.get_resolver_for_user(
        user_id=user_id,
        config=config,
        file_store=file_store,
    )

    # Create sandboxed conversation service through resolver
    service = resolver.resolve(sid=sid, user_id=user_id)

    # Connect to the sandboxed environment
    await service.connect()

    return service


async def create_sandboxed_conversation_unsecured(sid: str, user_id: str | None = None):
    """Example function showing how to create a sandboxed conversation using unsecured resolver."""
    config = OpenHandsConfig()
    file_store = InMemoryFileStore()

    # Use unsecured resolver (for internal usage only)
    resolver = SandboxedConversationServiceResolver.get_unsecured_resolver(
        config=config,
        file_store=file_store,
    )

    # Create sandboxed conversation service through resolver
    service = resolver.resolve(sid=sid, user_id=user_id)

    # Connect to the sandboxed environment
    await service.connect()

    return service


async def create_sandboxed_conversation_direct(sid: str, user_id: str | None = None):
    """Example function showing direct instantiation (deprecated pattern)."""
    config = OpenHandsConfig()
    file_store = InMemoryFileStore()

    # Direct instantiation (should be replaced with resolver pattern)
    service = SandboxedConversationService(
        sid=sid,
        file_store=file_store,
        config=config,
        user_id=user_id,
    )

    # Connect to the sandboxed environment
    await service.connect()

    return service


async def cleanup_sandboxed_conversation(service: SandboxedConversationService):
    """Example function showing how to cleanup a sandboxed conversation."""
    await service.disconnect()
