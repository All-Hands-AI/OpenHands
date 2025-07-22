from pydantic import BaseModel, Field, ValidationError


class ModelRoutingConfig(BaseModel):
    """Configuration for model routing.

    Attributes:
        prob_threshold (float): The probability threshold for routing decisions, used by `threshold_based_cv_router`.
        router_name (str): The name of the router to use. Default is 'noop_router'.
    """
    prob_threshold: float = Field(default=0.49414062500000006) # 60% calls to strong model
    router_name: str = Field(default='noop_router')

    model_config = {'extra': 'forbid'}

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'ModelRoutingConfig']:
        """
        Create a mapping of ModelRoutingConfig instances from a toml dictionary representing the [model_routing] section.

        The configuration is built from all keys in data.

        Returns:
            dict[str, ModelRoutingConfig]: A mapping where the key "model_routing" corresponds to the [model_routing] configuration
        """

        # Initialize the result mapping
        model_routing_mapping: dict[str, ModelRoutingConfig] = {}

        # Try to create the configuration instance
        try:
            model_routing_mapping['model_routing'] = cls.model_validate(data)
        except ValidationError as e:
            raise ValueError(f'Invalid model routing configuration: {e}')

        return model_routing_mapping
