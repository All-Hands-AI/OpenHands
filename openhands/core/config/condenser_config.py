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
    decay_rate: float = Field(
        default=0.5,
        description='Rate at which events are forgotten over time.',
        ge=0.0,
        le=1.0
    )
    min_events: int = Field(
        default=5,
        description='Minimum number of events to keep.',
        ge=1
    )


CondenserConfig = (
    NoOpCondenserConfig
    | RecentEventsCondenserConfig
    | LLMCondenserConfig
    | AmortizedForgettingCondenserConfig
)
