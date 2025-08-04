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

    tom_processed_data_dir: str = Field(
        default="./data/processed_data",
        description="Directory path for Tom agent processed data"
    )

    tom_user_model_dir: str = Field(
        default="./data/user_model",
        description="Directory path for Tom agent user models"
    )

    tom_enable_rag: bool = Field(
        default=True,
        description="Whether to enable RAG (Retrieval Augmented Generation) in Tom agent"
    )

    tom_user_id: Optional[str] = Field(
        default=None,
        description="User ID for Tom agent calls. If None, will be generated from session"
    )

    tom_fallback_on_error: bool = Field(
        default=True,
        description="Whether to continue with normal CodeAct behavior if Tom agent fails"
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

    tom_processed_data_dir: str = Field(
        default="./data/processed_data",
        description="Directory path for Tom agent processed data"
    )

    tom_user_model_dir: str = Field(
        default="./data/user_model",
        description="Directory path for Tom agent user models"
    )

    tom_enable_rag: bool = Field(
        default=True,
        description="Whether to enable RAG in Tom agent"
    )

    tom_user_id: Optional[str] = Field(
        default=None,
        description="User ID for Tom agent calls"
    )

    tom_fallback_on_error: bool = Field(
        default=True,
        description="Whether to fallback to normal behavior on Tom agent errors"
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
            tom_processed_data_dir=self.tom_processed_data_dir,
            tom_user_model_dir=self.tom_user_model_dir,
            tom_enable_rag=self.tom_enable_rag,
            tom_user_id=self.tom_user_id,
            tom_fallback_on_error=self.tom_fallback_on_error,
            tom_min_instruction_length=self.tom_min_instruction_length,
        )
