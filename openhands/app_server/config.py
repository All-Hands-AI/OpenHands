"""Configuration for the OpenHands App Server."""

import os
from pathlib import Path

from fastapi import Depends
from pydantic import Field

from openhands.agent_server.env_parser import from_env
from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoServiceManager,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationServiceManager,
)
from openhands.app_server.app_conversation.app_conversation_start_task_service import (
    AppConversationStartTaskServiceManager,
)
from openhands.app_server.app_lifespan.app_lifespan_service import AppLifespanService
from openhands.app_server.app_lifespan.oss_app_lifespan_service import (
    OssAppLifespanService,
)
from openhands.app_server.event.event_service import EventServiceManager
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackServiceManager,
)
from openhands.app_server.sandbox.sandbox_service import SandboxServiceManager
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecServiceManager
from openhands.app_server.services.db_service import DbService
from openhands.app_server.services.httpx_client_manager import HttpxClientManager
from openhands.app_server.services.jwt_service import JwtService, JwtServiceManager
from openhands.app_server.user.user_admin_service import UserAdminServiceManager
from openhands.app_server.user.user_service import UserServiceManager
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


class AppServerConfig(OpenHandsModel):
    persistence_dir: Path = Field(default_factory=get_default_persistence_dir)
    web_url: str | None = Field(
        default=None,
        description='The URL where OpenHands is running (e.g., http://localhost:3000)',
    )
    # Service managers
    event: EventServiceManager | None = None
    event_callback: EventCallbackServiceManager | None = None
    sandbox: SandboxServiceManager | None = None
    sandbox_spec: SandboxSpecServiceManager | None = None
    app_conversation_info: AppConversationInfoServiceManager | None = None
    app_conversation_start_task: AppConversationStartTaskServiceManager | None = None
    app_conversation: AppConversationServiceManager | None = None
    user: UserServiceManager | None = None
    user_admin: UserAdminServiceManager | None = None
    jwt: JwtServiceManager | None = None
    httpx: HttpxClientManager = Field(default_factory=HttpxClientManager)

    # Services
    lifespan: AppLifespanService = Field(default_factory=OssAppLifespanService)
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


def event_manager() -> EventServiceManager:
    config = get_global_config()
    event = config.event
    if event is None:
        from openhands.app_server.event.filesystem_event_service import (
            FilesystemEventServiceManager,
        )

        event = FilesystemEventServiceManager()
        config.event = event
    return event


def event_callback_manager() -> EventCallbackServiceManager:
    config = get_global_config()
    event_callback = config.event_callback
    if event_callback is None:
        from openhands.app_server.event_callback.sql_event_callback_service import (
            SQLEventCallbackServiceManager,
        )

        event_callback = SQLEventCallbackServiceManager()
        config.event_callback = event_callback
    return event_callback


def sandbox_manager() -> SandboxServiceManager:
    config = get_global_config()
    sandbox = config.sandbox
    if sandbox is None:
        if os.getenv('RUNTIME') == 'remote':
            from openhands.app_server.sandbox.remote_sandbox_service import (
                RemoteSandboxServiceManager,
            )

            sandbox = RemoteSandboxServiceManager()
        else:
            from openhands.app_server.sandbox.docker_sandbox_service import (
                DockerSandboxServiceManager,
            )

            sandbox = DockerSandboxServiceManager()
        config.sandbox = sandbox
    return sandbox


def sandbox_spec_manager() -> SandboxSpecServiceManager:
    config = get_global_config()
    sandbox_spec = config.sandbox_spec
    if sandbox_spec is None:
        if os.getenv('RUNTIME') == 'remote':
            from openhands.app_server.sandbox.remote_sandbox_spec_service import (
                RemoteSandboxSpecServiceManager,
            )

            sandbox_spec = RemoteSandboxSpecServiceManager()
        else:
            from openhands.app_server.sandbox.docker_sandbox_spec_service import (
                DockerSandboxSpecServiceManager,
            )

            sandbox_spec = DockerSandboxSpecServiceManager()
        config.sandbox_spec = sandbox_spec
    return sandbox_spec


def app_conversation_info_manager() -> AppConversationInfoServiceManager:
    config = get_global_config()
    app_conversation_info = config.app_conversation_info
    if app_conversation_info is None:
        from openhands.app_server.app_conversation.sql_app_conversation_info_service import (  # noqa: E501
            SQLAppConversationServiceManager,
        )

        app_conversation_info = SQLAppConversationServiceManager()
        config.app_conversation_info = app_conversation_info
    return app_conversation_info


def app_conversation_start_task_manager() -> AppConversationStartTaskServiceManager:
    config = get_global_config()
    app_conversation_start_task = config.app_conversation_start_task
    if app_conversation_start_task is None:
        from openhands.app_server.app_conversation.sql_app_conversation_start_task_service import (  # noqa: E501
            SQLAppConversationStartTaskServiceManager,
        )

        app_conversation_start_task = SQLAppConversationStartTaskServiceManager()
        config.app_conversation_start_task = app_conversation_start_task
    return app_conversation_start_task


def app_conversation_manager() -> AppConversationServiceManager:
    config = get_global_config()
    app_conversation = config.app_conversation
    if app_conversation is None:
        from openhands.app_server.app_conversation.live_status_app_conversation_service import (  # noqa: E501
            LiveStatusAppConversationServiceManager,
        )

        app_conversation = LiveStatusAppConversationServiceManager()
        config.app_conversation = app_conversation
    return app_conversation


def user_manager() -> UserServiceManager:
    config = get_global_config()
    user = config.user
    if user is None:
        from openhands.app_server.user.legacy_user_service import (
            LegacyUserServiceManager,
        )

        user = LegacyUserServiceManager()
        config.user = user
    return user


def user_admin_manager() -> UserAdminServiceManager:
    config = get_global_config()
    user_admin = config.user_admin
    if user_admin is None:
        from openhands.app_server.user.legacy_user_admin_service import (
            LegacyUserAdminServiceManager,
        )

        user_admin = LegacyUserAdminServiceManager()
        config.user_admin = user_admin
    return user_admin


def httpx_client_manager() -> HttpxClientManager:
    config = get_global_config()
    return config.httpx


def resolve_jwt_service(
    config: AppServerConfig = Depends(get_global_config),
) -> JwtService:
    resolver = config.jwt
    if resolver is None:
        resolver = JwtServiceManager(persistence_dir=config.persistence_dir)
        config.jwt = resolver
    return resolver.get_jwt_service()


def app_lifespan() -> AppLifespanService:
    config = get_global_config()
    return config.lifespan


def db_service() -> DbService:
    config = get_global_config()
    return config.db_service
