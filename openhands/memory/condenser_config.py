from pydantic import BaseModel, Field

from openhands.core.config.llm_config import LLMConfig


class CondenserConfig(BaseModel):
    """Base configuration for memory condensers.
    
    By default, creates a NoopCondenser that doesn't modify the events list.
    """
    type: str = Field("noop", description="Type of condenser to use")


class NoopCondenserConfig(CondenserConfig):
    """Configuration for NoopCondenser."""
    type: str = Field("noop", const=True)


class RecentEventsCondenserConfig(CondenserConfig):
    """Configuration for RecentEventsCondenser."""
    type: str = Field("recent", const=True)
    max_events: int = Field(10, description="Maximum number of events to keep", ge=1)


class LLMCondenserConfig(CondenserConfig):
    """Configuration for LLMCondenser."""
    type: str = Field("llm", const=True)
    llm_config: LLMConfig = Field(..., description="Configuration for the LLM to use for condensing")