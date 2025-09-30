from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SandboxSpecStatus(Enum):
    BUILDING = 'BUILDING'
    READY = 'READY'
    ERROR = 'ERROR'
    DELETING = 'DELETING'


class SandboxSpecInfo(BaseModel):
    """A template for creating a Sandbox (e.g: A Docker Image vs Container)."""

    id: str
    command: str
    created_at: datetime
    initial_env: dict[str, str] = Field(
        default_factory=dict, description='Initial Environment Variables'
    )
    working_dir: str = '/openhands/code'


class SandboxSpecInfoPage(BaseModel):
    items: list[SandboxSpecInfo]
    next_page_id: str | None = None
