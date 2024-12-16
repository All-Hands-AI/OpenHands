from typing import Literal

from pydantic import BaseModel, Field

from openhands.core.config.llm_config import LLMConfig


class NoOpCondenserConfig(BaseModel):
    """Configuration for NoOpCondenser."""

    type: Literal['noop'] = Field('noop')


class RecentEventsCondenserConfig(BaseModel):
    """Configuration for RecentEventsCondenser."""

    type: Literal['recent'] = Field('recent')
    keep_first: int = Field(
        default=0,
        description='The number of initial events to condense.',
    )
    max_events: int = Field(
        default=10, description='Maximum number of events to keep.', ge=1
    )


class LLMCondenserConfig(BaseModel):
    """Configuration for LLMCondenser."""

    type: Literal['llm'] = Field('llm')
    llm_config: LLMConfig = Field(
        ..., description='Configuration for the LLM to use for condensing.'
    )


class AmortizedForgettingCondenserConfig(BaseModel):
    """Configuration for AmortizedForgettingCondenser."""

    type: Literal['amortized'] = Field('amortized')
    max_size: int = Field(
        default=100,
        description='Maximum size of the condensed history before triggering forgetting.',
        ge=2
    )
    keep_first: int = Field(
        default=0,
        description='Number of initial events to always keep in history.',
        ge=0
    )


class LLMAttentionCondenserConfig(BaseModel):
    """Configuration for LLMAttentionCondenser."""

    type: Literal['llm_attention'] = Field('llm_attention')
    max_size: int = Field(
        default=100,
        description='Maximum size of the condensed history before triggering forgetting.',
        ge=2
    )
    keep_first: int = Field(
        default=0,
        description='Number of initial events to always keep in history.',
        ge=0
    )


CondenserConfig = (
    NoOpCondenserConfig
    | RecentEventsCondenserConfig
    | LLMCondenserConfig
    | AmortizedForgettingCondenserConfig
    | LLMAttentionCondenserConfig)
