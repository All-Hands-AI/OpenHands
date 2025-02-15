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
        # Build string representation using all model attributes from model_dump()
        data = self.model_dump()  # type: ignore
        attr_str = [f'{k}={repr(v)}' for k, v in data.items()]
        return f"ExtendedConfig({', '.join(attr_str)})"

    @classmethod
    def from_dict(cls, extended_config_dict: dict) -> 'ExtendedConfig':
        # Create an instance using Pydantic V2's model validation
        return cls.model_validate(extended_config_dict)

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, key: str) -> object:
        # Allow dictionary-like access to attributes using model_dump()
        return self.model_dump()[key]  # type: ignore

    def __getattr__(self, key: str) -> object:
        # Fallback for attribute access if the attribute is not found normally
        data = self.model_dump()  # type: ignore
        try:
            return data[key]
        except KeyError as e:
            raise AttributeError(
                f"'ExtendedConfig' object has no attribute '{key}'"
            ) from e
