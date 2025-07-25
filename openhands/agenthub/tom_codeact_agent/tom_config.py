"""Configuration for TomCodeActAgent."""

from typing import Optional

from pydantic import BaseModel, Field

from openhands.core.config import AgentConfig


class TomConfig(BaseModel):
    """Configuration for Tom agent integration."""
    
    enable_tom_integration: bool = Field(
        default=False,
        description="Whether to enable Tom agent integration for personalized guidance"
    )
    
    tom_api_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of the Tom API server"
    )
    
    tom_user_id: Optional[str] = Field(
        default=None,
        description="User ID for Tom API calls. If None, will be generated from session"
    )
    
    tom_timeout: int = Field(
        default=30,
        description="Timeout for Tom API requests in seconds"
    )
    
    tom_fallback_on_error: bool = Field(
        default=True,
        description="Whether to continue with normal CodeAct behavior if Tom API fails"
    )
    
    tom_min_instruction_length: int = Field(
        default=5,
        description="Minimum length of user instruction to trigger Tom improvement"
    )


class TomCodeActAgentConfig(AgentConfig):
    """Configuration for TomCodeActAgent that extends base AgentConfig."""
    
    # Tom-specific configuration
    enable_tom_integration: bool = Field(
        default=False,
        description="Whether to enable Tom agent integration"
    )
    
    tom_api_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of the Tom API server"
    )
    
    tom_user_id: Optional[str] = Field(
        default=None,
        description="User ID for Tom API calls"
    )
    
    tom_timeout: int = Field(
        default=30,
        description="Timeout for Tom API requests in seconds"
    )
    
    tom_fallback_on_error: bool = Field(
        default=True,
        description="Whether to fallback to normal behavior on Tom API errors"
    )
    
    tom_min_instruction_length: int = Field(
        default=5,
        description="Minimum instruction length to trigger Tom improvement"
    )
    
    @property
    def tom_config(self) -> TomConfig:
        """Get Tom configuration as a separate object."""
        return TomConfig(
            enable_tom_integration=self.enable_tom_integration,
            tom_api_url=self.tom_api_url,
            tom_user_id=self.tom_user_id,
            tom_timeout=self.tom_timeout,
            tom_fallback_on_error=self.tom_fallback_on_error,
            tom_min_instruction_length=self.tom_min_instruction_length,
        )