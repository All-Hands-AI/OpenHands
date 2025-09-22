from typing import Optional

from pydantic import BaseModel, Field


class TokenUsageResponse(BaseModel):
    """Response model for token usage metrics."""

    model: str = Field(default='', description='The LLM model used')
    prompt_tokens: int = Field(default=0, description='Number of tokens in the prompt')
    completion_tokens: int = Field(
        default=0, description='Number of tokens in the completion'
    )
    cache_read_tokens: int = Field(
        default=0, description='Number of tokens read from cache'
    )
    cache_write_tokens: int = Field(
        default=0, description='Number of tokens written to cache'
    )
    context_window: int = Field(default=0, description='Total context window size')
    per_turn_token: int = Field(
        default=0, description='Tokens used in the current turn'
    )


class CostResponse(BaseModel):
    """Response model for cost metrics."""

    model: str = Field(description='The LLM model used')
    cost: float = Field(description='Cost for this specific call')
    timestamp: float = Field(description='Timestamp when the cost was recorded')


class ResponseLatencyResponse(BaseModel):
    """Response model for response latency metrics."""

    model: str = Field(description='The LLM model used')
    latency: float = Field(description='Response latency in seconds')
    response_id: str = Field(description='Unique identifier for this response')


class MetricsResponse(BaseModel):
    """Response model for comprehensive metrics data."""

    accumulated_cost: float = Field(default=0.0, description='Total accumulated cost')
    max_budget_per_task: Optional[float] = Field(
        default=None, description='Maximum budget per task'
    )
    accumulated_token_usage: TokenUsageResponse = Field(
        description='Accumulated token usage across all calls'
    )
    costs: list[CostResponse] = Field(
        default_factory=list, description='List of individual cost entries'
    )
    response_latencies: list[ResponseLatencyResponse] = Field(
        default_factory=list, description='List of response latency entries'
    )
    token_usages: list[TokenUsageResponse] = Field(
        default_factory=list, description='List of individual token usage entries'
    )


class ConversationMetricsResponse(BaseModel):
    """Response model for conversation-level metrics."""

    conversation_id: str = Field(description='The conversation ID')
    metrics: Optional[MetricsResponse] = Field(
        default=None, description='Combined metrics for the conversation'
    )
    service_metrics: dict[str, MetricsResponse] = Field(
        default_factory=dict, description='Metrics broken down by service ID'
    )
    has_active_session: bool = Field(
        default=False, description='Whether the conversation has an active session'
    )
