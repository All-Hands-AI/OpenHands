"""Configuration for the OpenHands App Server."""

import os
from pathlib import Path
from typing import Awaitable, Callable

import httpx
from pydantic import Field

from openhands.agent_server.env_parser import from_env
from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
    AppConversationInfoServiceInjector,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationServiceInjector,
)
from openhands.app_server.app_conversation.app_conversation_start_task_service import (
    AppConversationStartTaskService,
    AppConversationStartTaskServiceInjector,
)
from openhands.app_server.app_lifespan.app_lifespan_service import AppLifespanService
from openhands.app_server.app_lifespan.oss_app_lifespan_service import (
    OssAppLifespanService,
)
from openhands.app_server.event.event_service import EventServiceInjector
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackService,
    EventCallbackServiceInjector,
)
from openhands.app_server.sandbox.sandbox_service import (
    SandboxService,
    SandboxServiceInjector,
)
from openhands.app_server.sandbox.sandbox_spec_service import (
    SandboxSpecService,
    SandboxSpecServiceInjector,
)
from openhands.app_server.services.db_service import DbService
from openhands.app_server.services.httpx_client_injector import HttpxClientInjector
from openhands.app_server.services.jwt_service import JwtService, JwtServiceInjector
from openhands.app_server.user.user_context import UserContext, UserContextInjector
from openhands.sdk.utils.models import OpenHandsModel


def get_default_persistence_dir() -> Path:
    # Recheck env because this function is also used to generate other defaults
    persistence_dir = os.getenv('OH_PERSISTENCE_DIR')

    if persistence_dir:
        result = Path(persistence_dir)
    else:
        result = Path.home() / '.openhands'

    result.mkdir(parents=True, exist_ok=True)
    return result


def get_default_web_url() -> str | None:
    """Get legacy web host parameter.

    If present, we assume we are running under https."""
    web_host = os.getenv('WEB_HOST')
    if not web_host:
        return None
    return f'https://{web_host}'


def _get_default_lifespan():
    # Check legacy parameters for saas mode. If we are in SAAS mode do not apply
    # OSS alembic migrations
    if 'saas' in (os.getenv('OPENHANDS_CONFIG_CLS') or '').lower():
        return None
    return OssAppLifespanService()


class AppServerConfig(OpenHandsModel):
    persistence_dir: Path = Field(default_factory=get_default_persistence_dir)
    web_url: str | None = Field(
        default_factory=get_default_web_url,
        description='The URL where OpenHands is running (e.g., http://localhost:3000)',
    )
    # Service injectors
    event: EventServiceInjector | None = None
    event_callback: EventCallbackServiceInjector | None = None
    sandbox: SandboxServiceInjector | None = None
    sandbox_spec: SandboxSpecServiceInjector | None = None
    app_conversation_info: AppConversationInfoServiceInjector | None = None
    app_conversation_start_task: AppConversationStartTaskServiceInjector | None = None
    app_conversation: AppConversationServiceInjector | None = None
    user: UserContextInjector | None = None
    jwt: JwtServiceInjector | None = None
    httpx: HttpxClientInjector = Field(default_factory=HttpxClientInjector)

    # Services
    lifespan: AppLifespanService = Field(default_factory=_get_default_lifespan)
    db_service: DbService = Field(
        default_factory=lambda: DbService(persistence_dir=get_default_persistence_dir())
    )


_global_config: AppServerConfig | None = None


def get_global_config() -> AppServerConfig:
    """Get the default local server config shared across the server."""
    global _global_config
    if _global_config is None:
        # Load configuration from environment...
        _global_config = from_env(AppServerConfig, 'OH')  # type: ignore

    return _global_config  # type: ignore


def event_injector() -> Callable[
    ..., EventServiceInjector | Awaitable[EventServiceInjector]
]:
    config = get_global_config()
    event = config.event
    if event is None:
        from openhands.app_server.event.filesystem_event_service import (
            FilesystemEventServiceInjector,
        )

        event = FilesystemEventServiceInjector()
        config.event = event
    return event


def event_callback_injector() -> Callable[
    ..., EventCallbackService | Awaitable[EventCallbackService]
]:
    config = get_global_config()
    event_callback = config.event_callback
    if event_callback is None:
        from openhands.app_server.event_callback.sql_event_callback_service import (
            SQLEventCallbackServiceInjector,
        )

        event_callback = SQLEventCallbackServiceInjector()
        config.event_callback = event_callback
    return event_callback.get_injector()


def sandbox_injector() -> Callable[..., SandboxService | Awaitable[SandboxService]]:
    config = get_global_config()
    sandbox = config.sandbox
    if sandbox is None:
        # Legacy fallback
        if os.getenv('RUNTIME') == 'remote':
            from openhands.app_server.sandbox.remote_sandbox_service import (
                RemoteSandboxServiceInjector,
            )

            sandbox = RemoteSandboxServiceInjector(
                api_key=os.environ['SANDBOX_API_KEY'],
                api_url=os.environ['SANDBOX_REMOTE_RUNTIME_API_URL'],
            )
        else:
            from openhands.app_server.sandbox.docker_sandbox_service import (
                DockerSandboxServiceInjector,
            )

            sandbox = DockerSandboxServiceInjector()
        config.sandbox = sandbox
    return sandbox.get_injector()


def sandbox_spec_injector() -> Callable[
    ..., SandboxSpecService | Awaitable[SandboxSpecService]
]:
    config = get_global_config()
    sandbox_spec = config.sandbox_spec
    if sandbox_spec is None:
        if os.getenv('RUNTIME') == 'remote':
            from openhands.app_server.sandbox.remote_sandbox_spec_service import (
                RemoteSandboxSpecServiceInjector,
            )

            sandbox_spec = RemoteSandboxSpecServiceInjector()
        else:
            from openhands.app_server.sandbox.docker_sandbox_spec_service import (
                DockerSandboxSpecServiceInjector,
            )

            sandbox_spec = DockerSandboxSpecServiceInjector()
        config.sandbox_spec = sandbox_spec
    return sandbox_spec.get_injector()


def app_conversation_info_injector() -> Callable[
    ..., AppConversationInfoService | Awaitable[AppConversationInfoService]
]:
    config = get_global_config()
    app_conversation_info = config.app_conversation_info
    if app_conversation_info is None:
        from openhands.app_server.app_conversation.sql_app_conversation_info_service import (  # noqa: E501
            SQLAppConversationInfoServiceInjector,
        )

        app_conversation_info = SQLAppConversationInfoServiceInjector()
        config.app_conversation_info = app_conversation_info
    return app_conversation_info.get_injector()


def app_conversation_start_task_injector() -> Callable[
    ..., AppConversationStartTaskService | Awaitable[AppConversationStartTaskService]
]:
    config = get_global_config()
    app_conversation_start_task = config.app_conversation_start_task
    if app_conversation_start_task is None:
        from openhands.app_server.app_conversation.sql_app_conversation_start_task_service import (  # noqa: E501
            SQLAppConversationStartTaskServiceInjector,
        )

        app_conversation_start_task = SQLAppConversationStartTaskServiceInjector()
        config.app_conversation_start_task = app_conversation_start_task
    return app_conversation_start_task.get_injector()


def app_conversation_injector() -> AppConversationServiceInjector:
    config = get_global_config()
    app_conversation = config.app_conversation
    if app_conversation is None:
        from openhands.app_server.app_conversation.live_status_app_conversation_service import (  # noqa: E501
            LiveStatusAppConversationServiceInjector,
        )

        app_conversation = LiveStatusAppConversationServiceInjector()
        config.app_conversation = app_conversation
    return app_conversation


def user_injector() -> Callable[..., UserContext | Awaitable[UserContext]]:
    config = get_global_config()
    user = config.user
    if user is None:
        from openhands.app_server.user.auth_user_context import (
            AuthUserContextInjector,
        )

        user = AuthUserContextInjector()
        config.user = user
    return user.get_injector()


def httpx_client_injector() -> Callable[
    ..., httpx.AsyncClient | Awaitable[httpx.AsyncClient]
]:
    config = get_global_config()
    return config.httpx.resolve


def jwt_service() -> JwtService:
    config = get_global_config()
    resolver = config.jwt
    if resolver is None:
        resolver = JwtServiceInjector(persistence_dir=config.persistence_dir)
        config.jwt = resolver
    return resolver.get_jwt_service()


def app_lifespan() -> AppLifespanService:
    config = get_global_config()
    return config.lifespan


def db_service() -> DbService:
    config = get_global_config()
    return config.db_service
