from dataclasses import dataclass, fields

from openhands.core.config.config_utils import get_field_info

REPLAY_SENSITIVE_FIELDS = ['api_key']

@dataclass
class ReplayConfig:
    """Configuration for the replay api.

    Attributes:
        api_key: The API key to use for the replay API.
        dir: The parent directory of both devtools and replayapi git repositories.
    """

    api_key: str | None = None
    dir: str | None = None

    def defaults_to_dict(self) -> dict:
        """Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional."""
        result = {}
        for f in fields(self):
            result[f.name] = get_field_info(f)
        return result

    def to_safe_dict(self):
        """Return a dict with the sensitive fields replaced with ******."""
        ret = self.__dict__.copy()
        for k, v in ret.items():
            if k in REPLAY_SENSITIVE_FIELDS:
                ret[k] = '******' if v else None
            elif isinstance(v, ReplayConfig):
                ret[k] = v.to_safe_dict()
        return ret

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"ReplayConfig({', '.join(attr_str)})"
