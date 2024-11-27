from typing import Literal

from pydantic import BaseModel, Field

from openhands.core.config.llm_config import LLMConfig


class CondenserConfig(BaseModel):
    """Base configuration for memory condensers.

    By default, creates a NoOpCondenser that doesn't modify the events list.
    """

    type: str = Field(default='noop', description='Type of condenser to use.')


class NoOpCondenserConfig(CondenserConfig):
    """Configuration for NoOpCondenser."""

    type: Literal['noop'] = Field('noop')


class RecentEventsCondenserConfig(CondenserConfig):
    """Configuration for RecentEventsCondenser."""

    type: Literal['recent'] = Field('recent')
    max_events: int = Field(
        default=10, description='Maximum number of events to keep.', ge=1
    )


class LLMCondenserConfig(CondenserConfig):
    """Configuration for LLMCondenser."""

    type: Literal['llm'] = Field('llm')
    llm_config: LLMConfig = Field(
        ..., description='Configuration for the LLM to use for condensing.'
    )
