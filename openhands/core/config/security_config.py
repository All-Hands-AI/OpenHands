from dataclasses import dataclass, fields

from openhands.core.config.config_utils import get_field_info


@dataclass
class SecurityConfig:
    """Configuration for security related functionalities.

    Attributes:
        confirmation_mode: Whether to enable confirmation mode.
        security_analyzer: The security analyzer to use.
    """

    confirmation_mode: bool = False
    security_analyzer: str | None = None

    def defaults_to_dict(self) -> dict:
        """Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional."""
        dict = {}
        for f in fields(self):
            dict[f.name] = get_field_info(f)
        return dict

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"SecurityConfig({', '.join(attr_str)})"

    @classmethod
    def from_dict(cls, security_config_dict: dict) -> 'SecurityConfig':
        return cls(**security_config_dict)

    def __repr__(self):
        return self.__str__()
