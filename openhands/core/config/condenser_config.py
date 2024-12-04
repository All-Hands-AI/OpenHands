from typing import Literal

from pydantic import BaseModel, Field

from openhands.core.config.llm_config import LLMConfig


class NoOpCondenserConfig(BaseModel):
    """Configuration for NoOpCondenser."""

    type: Literal['noop'] = Field('noop')


class RecentEventsCondenserConfig(BaseModel):
    """Configuration for RecentEventsCondenser."""

    type: Literal['recent'] = Field('recent')
    max_events: int = Field(
        default=10, description='Maximum number of events to keep.', ge=1
    )


class LLMCondenserConfig(BaseModel):
    """Configuration for LLMCondenser."""

    type: Literal['llm'] = Field('llm')
    llm_config: LLMConfig = Field(
        ..., description='Configuration for the LLM to use for condensing.'
    )


CondenserConfig = NoOpCondenserConfig | RecentEventsCondenserConfig | LLMCondenserConfig
