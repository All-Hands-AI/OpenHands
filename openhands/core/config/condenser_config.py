from typing import Literal, cast

from pydantic import BaseModel, Field, ValidationError

from openhands.core.config.llm_config import LLMConfig


class NoOpCondenserConfig(BaseModel):
    """Configuration for NoOpCondenser."""

    type: Literal['noop'] = Field('noop')

    model_config = {'extra': 'forbid'}


class ObservationMaskingCondenserConfig(BaseModel):
    """Configuration for ObservationMaskingCondenser."""

    type: Literal['observation_masking'] = Field('observation_masking')
    attention_window: int = Field(
        default=10,
        description='The number of most-recent events where observations will not be masked.',
        ge=1,
    )

    model_config = {'extra': 'forbid'}


class RecentEventsCondenserConfig(BaseModel):
    """Configuration for RecentEventsCondenser."""

    type: Literal['recent'] = Field('recent')

    # at least one event by default, because the best guess is that it is the user task
    keep_first: int = Field(
        default=1,
        description='The number of initial events to condense.',
        ge=0,
    )
    max_events: int = Field(
        default=10, description='Maximum number of events to keep.', ge=1
    )

    model_config = {'extra': 'forbid'}


class LLMSummarizingCondenserConfig(BaseModel):
    """Configuration for LLMCondenser."""

    type: Literal['llm'] = Field('llm')
    llm_config: LLMConfig = Field(
        ..., description='Configuration for the LLM to use for condensing.'
    )

    # at least one event by default, because the best guess is that it's the user task
    keep_first: int = Field(
        default=1,
        description='The number of initial events to condense.',
        ge=0,
    )
    max_size: int = Field(
        default=100,
        description='Maximum size of the condensed history before triggering forgetting.',
        ge=2,
    )

    model_config = {'extra': 'forbid'}


class AmortizedForgettingCondenserConfig(BaseModel):
    """Configuration for AmortizedForgettingCondenser."""

    type: Literal['amortized'] = Field('amortized')
    max_size: int = Field(
        default=100,
        description='Maximum size of the condensed history before triggering forgetting.',
        ge=2,
    )

    # at least one event by default, because the best guess is that it's the user task
    keep_first: int = Field(
        default=1,
        description='The number of initial events to condense.',
        ge=0,
    )

    model_config = {'extra': 'forbid'}


class LLMAttentionCondenserConfig(BaseModel):
    """Configuration for LLMAttentionCondenser."""

    type: Literal['llm_attention'] = Field('llm_attention')
    llm_config: LLMConfig = Field(
        ..., description='Configuration for the LLM to use for attention.'
    )
    max_size: int = Field(
        default=100,
        description='Maximum size of the condensed history before triggering forgetting.',
        ge=2,
    )

    # at least one event by default, because the best guess is that it's the user task
    keep_first: int = Field(
        default=1,
        description='The number of initial events to condense.',
        ge=0,
    )

    model_config = {'extra': 'forbid'}


# Type alias for convenience
CondenserConfig = (
    NoOpCondenserConfig
    | ObservationMaskingCondenserConfig
    | RecentEventsCondenserConfig
    | LLMSummarizingCondenserConfig
    | AmortizedForgettingCondenserConfig
    | LLMAttentionCondenserConfig
)


def from_toml_section(data: dict) -> dict[str, CondenserConfig]:
    """
    Create a mapping of CondenserConfig instances from a toml dictionary representing the [condenser] section.

    For CondenserConfig, the handling is different since it's a union type. The type of condenser
    is determined by the 'type' field in each section.

    Example:
    Parse condenser configs like:
        [condenser]
        type = "noop"
        [condenser.agent1]
        type = "recent"
        keep_first = 2
        max_events = 20

    Returns:
        dict[str, CondenserConfig]: A mapping where the key "condenser" corresponds to the default configuration
        and additional keys represent custom configurations.
    """
    from openhands.core import logger

    # Initialize the result mapping
    condenser_mapping: dict[str, CondenserConfig] = {}

    # Extract base config data (non-dict values) and custom sections
    base_data = {}
    custom_sections: dict[str, dict] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            custom_sections[key] = value
        else:
            base_data[key] = value

    # Process base config
    try:
        # Determine which condenser type to use based on 'type' field
        base_type = base_data.get('type', 'noop')
        base_config = create_condenser_config(base_type, base_data)
        condenser_mapping['condenser'] = base_config
    except (ValidationError, ValueError) as e:
        logger.openhands_logger.warning(
            f'Invalid base condenser configuration: {e}. Using NoOpCondenserConfig.'
        )
        # Default to NoOpCondenserConfig if base config fails
        base_config = NoOpCondenserConfig()
        condenser_mapping['condenser'] = base_config

    # Process each custom section independently
    for name, section_data in custom_sections.items():
        try:
            # Determine which condenser type to use based on 'type' field
            section_type = section_data.get('type', 'noop')
            custom_config = create_condenser_config(section_type, section_data)
            condenser_mapping[name] = custom_config
        except (ValidationError, ValueError) as e:
            logger.openhands_logger.warning(
                f'Invalid condenser configuration for [{name}]: {e}. This section will be skipped.'
            )
            # Skip this custom section but continue with others
            continue

    return condenser_mapping


def create_condenser_config(condenser_type: str, data: dict) -> CondenserConfig:
    """
    Create a CondenserConfig instance based on the specified type.

    Args:
        condenser_type: The type of condenser to create.
        data: The configuration data.

    Returns:
        A CondenserConfig instance.

    Raises:
        ValueError: If the condenser type is unknown.
        ValidationError: If the provided data fails validation for the condenser type.
    """
    # Map condenser type to the appropriate class
    condenser_classes = {
        'noop': NoOpCondenserConfig,
        'observation_masking': ObservationMaskingCondenserConfig,
        'recent': RecentEventsCondenserConfig,
        'llm': LLMSummarizingCondenserConfig,
        'amortized': AmortizedForgettingCondenserConfig,
        'llm_attention': LLMAttentionCondenserConfig,
    }

    if condenser_type not in condenser_classes:
        raise ValueError(f'Unknown condenser type: {condenser_type}')

    # Create and validate the config using direct instantiation
    # Explicitly handle ValidationError to provide more context
    try:
        config_class = condenser_classes[condenser_type]
        # Use type casting to help mypy understand the return type
        return cast(CondenserConfig, config_class(**data))
    except ValidationError as e:
        # Re-raise the ValidationError with more context about which condenser type failed
        raise ValidationError(
            f"Validation failed for condenser type '{condenser_type}': {e}",
            e.errors(),
        )
