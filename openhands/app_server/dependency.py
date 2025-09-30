import logging
from dataclasses import dataclass

import httpx

from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoServiceResolver,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationServiceResolver,
)
from openhands.app_server.config import get_global_config
from openhands.app_server.event.event_service import EventServiceResolver
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackServiceResolver,
)
from openhands.app_server.sandbox.sandbox_service import SandboxServiceResolver
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecServiceResolver
from openhands.app_server.user.user_service import UserServiceResolver

_logger = logging.getLogger(__name__)


@dataclass
class DependencyResolver:
    """Object for exposing dependencies and preventing circular imports and lookups."""

    event: EventServiceResolver
    event_callback: EventCallbackServiceResolver
    sandbox: SandboxServiceResolver
    sandbox_spec: SandboxSpecServiceResolver
    app_conversation_info: AppConversationInfoServiceResolver
    app_conversation: AppConversationServiceResolver
    user: UserServiceResolver


_dependency_resolver: DependencyResolver | None = None


def get_dependency_resolver():
    """Get the dependency manager, lazily initializing on first invocation."""
    global _dependency_resolver
    if not _dependency_resolver:
        config = get_global_config()
        _dependency_resolver = DependencyResolver(
            event=config.event or _get_event_service_resolver(),
            event_callback=config.event_callback
            or _get_event_callback_service_resolver(),
            sandbox=config.sandbox or _get_sandbox_service_resolver(),
            sandbox_spec=config.sandbox_spec or _get_sandbox_spec_service_resolver(),
            app_conversation_info=config.app_conversation_info
            or _get_app_conversation_info_service_resolver(),
            app_conversation=config.app_conversation
            or _get_app_conversation_service_resolver(),
            user=config.user or _get_user_service_resolver(),
        )
    return _dependency_resolver


# TODO: have this initialize as part of the app lifespan
_httpx_client: httpx.AsyncClient | None = None


def get_httpx_client() -> httpx.AsyncClient:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient()
    return _httpx_client


def _get_event_service_resolver():
    from openhands.app_server.event.filesystem_event_service import (
        FilesystemEventServiceResolver,
    )

    return FilesystemEventServiceResolver()


def _get_event_callback_service_resolver():
    from openhands.app_server.event_callback.sql_event_callback_service import (
        SQLEventCallbackServiceResolver,
    )

    return SQLEventCallbackServiceResolver()


def _get_sandbox_service_resolver():
    from openhands.app_server.sandbox import (
        docker_sandbox_service as ctx,
    )

    return ctx.DockerSandboxServiceResolver()


def _get_sandbox_spec_service_resolver():
    from openhands.app_server.sandbox import (
        docker_sandbox_spec_service as ctx,
    )

    return ctx.DockerSandboxSpecServiceResolver()


def _get_app_conversation_info_service_resolver():
    from openhands.app_server.app_conversation.sql_app_conversation_info_service import (  # noqa: E501
        SQLAppConversationServiceResolver,
    )

    return SQLAppConversationServiceResolver()


def _get_app_conversation_service_resolver():
    from openhands.app_server.app_conversation.live_status_app_conversation_service import (  # noqa: E501
        LiveStatusAppConversationServiceResolver,
    )

    return LiveStatusAppConversationServiceResolver()


def _get_user_service_resolver():
    from openhands.app_server.user.legacy_user_service import (
        LegacyUserServiceResolver,
    )

    return LegacyUserServiceResolver()
