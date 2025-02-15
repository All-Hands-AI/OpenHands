from pydantic import BaseModel


class ExtendedConfig(BaseModel):
    """Configuration for extended functionalities.

    Attributes:
        Values depend on the defined section
    """

    # No explicit fields are defined; extra keys will be allowed via the model configuration.

    class Config:
        extra = 'allow'  # allow arbitrary extra fields

    def __str__(self) -> str:
        # Build string representation using all model attributes
        attr_str = []
        # __dict__ contains both declared and extra attributes
        for attr_name, attr_value in self.__dict__.items():
            attr_str.append(f'{attr_name}={repr(attr_value)}')
        return f"ExtendedConfig({', '.join(attr_str)})"

    @classmethod
    def from_dict(cls, extended_config_dict: dict) -> 'ExtendedConfig':
        # Create an instance using Pydantic V2's model validation
        return cls.model_validate(extended_config_dict)

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, key: str) -> object:
        # Allow dictionary-like access to attributes
        return self.__dict__[key]

    def __getattr__(self, key: str) -> object:
        # Fallback for attribute access if the attribute is not found normally
        try:
            return self.__dict__[key]
        except KeyError as e:
            raise AttributeError(
                f"'ExtendedConfig' object has no attribute '{key}'"
            ) from e
