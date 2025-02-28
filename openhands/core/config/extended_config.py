from pydantic import RootModel


class ExtendedConfig(RootModel[dict]):
    """Configuration for extended functionalities.

    This is implemented as a root model so that the entire input is stored
    as the root value. This allows arbitrary keys to be stored and later
    accessed via attribute or dictionary-style access.
    """

    @property
    def root(self) -> dict:  # type annotation to help mypy
        return super().root

    def __str__(self) -> str:
        # Use the root dict to build a string representation.
        attr_str = [f'{k}={repr(v)}' for k, v in self.root.items()]
        return f"ExtendedConfig({', '.join(attr_str)})"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_dict(cls, data: dict) -> 'ExtendedConfig':
        # Create an instance directly by wrapping the input dict.
        return cls(data)

    def __getitem__(self, key: str) -> object:
        # Provide dictionary-like access via the root dict.
        return self.root[key]

    def __getattr__(self, key: str) -> object:
        # Fallback for attribute access using the root dict.
        try:
            return self.root[key]
        except KeyError as e:
            raise AttributeError(
                f"'ExtendedConfig' object has no attribute '{key}'"
            ) from e
