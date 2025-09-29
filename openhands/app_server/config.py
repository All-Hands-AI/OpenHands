"""Configuration for the OpenHands App Server"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import base62
from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    TypeAdapter,
    field_serializer,
)

from openhands.agent_server.env_parser import from_env
from openhands.app_server.conversation.sandboxed_conversation_info_service import (
    SandboxedConversationInfoServiceResolver,
)
from openhands.app_server.conversation.sandboxed_conversation_service import (
    SandboxedConversationServiceResolver,
)
from openhands.app_server.event.event_service import EventServiceResolver
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackServiceResolver,
)
from openhands.app_server.sandbox.sandbox_service import SandboxServiceResolver
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecServiceResolver
from openhands.app_server.user.user_service import UserServiceResolver
from openhands.app_server.utils.date_utils import utc_now
from openhands.sdk.utils.models import OpenHandsModel

# Environment variable constants
GCP_REGION = os.environ.get('GCP_REGION')


def _get_db_url() -> SecretStr:
    url = os.environ.get('DB_URL')
    if url:
        return SecretStr(url)

    # Legacy fallback
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT', '5432')
    name = os.getenv('DB_NAME', 'openhands')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASS', 'postgres')
    if host:
        return SecretStr(f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}')

    # Default to sqlite
    return SecretStr('sqlite+aiosqlite:///./openhands.db')


def _get_default_workspace_dir() -> Path:
    # Recheck env because this function is also used to generate other defaults
    workspace_dir = os.getenv('OH_WORKSPACE_DIR')

    if not workspace_dir:
        # TODO: I suppose Could also default this to ~home/.openhands
        workspace_dir = 'workspace'

    result = Path(workspace_dir)
    result.mkdir(parents=True, exist_ok=True)
    return result


class EncryptionKey(BaseModel):
    """Configuration for an encryption key."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: SecretStr
    active: bool = True
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_serializer('key')
    def serialize_key(self, key: SecretStr, info: Any):
        """Conditionally serialize the key based on context."""
        if info.context and info.context.get('reveal_secrets'):
            return key.get_secret_value()
        return str(key)  # Returns '**********' by default


def _get_default_encryption_keys() -> list[EncryptionKey]:
    """Generate default encryption keys."""
    master_key = os.getenv('JWT_SECRET')
    if master_key:
        return [
            EncryptionKey(
                key=SecretStr(master_key),
                active=True,
                notes='jwt secret master key',
            )
        ]

    key_file = _get_default_workspace_dir() / '.keys'
    type_adapter = TypeAdapter(list[EncryptionKey])
    if key_file.exists():
        encryption_keys = type_adapter.validate_json(key_file.read_text())
        return encryption_keys

    encryption_keys = [
        EncryptionKey(
            key=SecretStr(base62.encodebytes(os.urandom(32))),
            active=True,
            notes='generated master key',
        )
    ]
    json_data = type_adapter.dump_json(
        encryption_keys, context={'expose_secrets': True}
    )
    key_file.write_bytes(json_data)
    return encryption_keys


class GCPConfig(BaseModel):
    project: str | None = os.getenv('GCP_PROJECT')
    region: str | None = os.getenv('GCP_REGION')


class DatabaseConfig(BaseModel):
    """Configuration specific to the database"""

    url: SecretStr = _get_db_url()
    name: str | None = os.getenv('DB_NAME')
    user: str | None = os.getenv('DB_USER')
    password: SecretStr | None = (
        SecretStr(os.environ['DB_PASSWORD']) if os.getenv('DB_PASSWORD') else None
    )
    echo: bool = False
    gcp_db_instance: str | None = os.getenv('GCP_DB_INSTANCE')
    pool_size: int = int(os.environ.get('DB_POOL_SIZE', '25'))
    max_overflow: int = int(os.environ.get('DB_MAX_OVERFLOW', '10'))

    @field_serializer('url', 'password')
    def serialize_key(self, value: SecretStr, info: Any):
        """Conditionally serialize the key based on context."""
        if info.context and info.context.get('reveal_secrets'):
            return value.get_secret_value()
        return str(value)  # Returns '**********' by default


class AppServerConfig(OpenHandsModel):
    encryption_keys: list[EncryptionKey] = Field(
        default_factory=_get_default_encryption_keys
    )
    workspace_dir: Path = Field(default_factory=_get_default_workspace_dir)
    web_url: str = Field(
        default='http://localhost:3000',
        description='The URL where OpenHands is running (e.g., http://localhost:3000)',
    )
    event: EventServiceResolver | None = None
    event_callback: EventCallbackServiceResolver | None = None
    sandbox: SandboxServiceResolver | None = None
    sandbox_spec: SandboxSpecServiceResolver | None = None
    sandboxed_conversation_info: SandboxedConversationInfoServiceResolver | None = None
    sandboxed_conversation: SandboxedConversationServiceResolver | None = None
    user: UserServiceResolver | None = None
    allow_cors_origins: list[str] = Field(
        default_factory=list,
        description=(
            'Set of CORS origins permitted by this server (Anything from localhost is '
            "always accepted regardless of what's in here)."
        ),
    )
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    gcp: GCPConfig = Field(default_factory=GCPConfig)


_global_config: AppServerConfig | None = None


def get_global_config() -> AppServerConfig:
    """Get the default local server config shared across the server"""
    global _global_config
    if _global_config is None:
        # Load configuration from environment...
        _global_config = from_env(AppServerConfig, 'OH')  # type: ignore

    return _global_config  # type: ignore
