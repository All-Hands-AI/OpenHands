from __future__ import annotations

import os
from typing import Any

import toml
from pydantic import SecretStr

from openhands.core import logger
from openhands.core.config.llm_config import LLMConfig


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _serialize_value(v: Any) -> Any:
    if isinstance(v, SecretStr):
        return v.get_secret_value()
    return v


def _serialize_dict(d: dict[str, Any]) -> dict[str, Any]:
    return {k: _serialize_value(v) for k, v in d.items()}


class TOMLConfigWriter:
    """Simple TOML writer for OpenHands config.

    It loads an existing TOML file if present, applies updates, and writes back.
    This implementation does not preserve comments but avoids overwriting unrelated
    sections by merging keys.
    """

    def __init__(self, toml_file: str = 'config.toml') -> None:
        self.toml_file = toml_file
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self.toml_file, 'r', encoding='utf-8') as f:
                self._data = toml.load(f)
        except FileNotFoundError:
            self._data = {}
        except toml.TomlDecodeError as e:
            logger.openhands_logger.warning(
                f'Cannot parse existing TOML at {self.toml_file}: {e}. Recreating file.'
            )
            self._data = {}

    def _ensure_section(self, name: str) -> dict[str, Any]:
        section = self._data.get(name)
        if not isinstance(section, dict):
            section = {}
            self._data[name] = section
        return section

    def update_core(self, data: dict[str, Any]) -> None:
        core = self._ensure_section('core')
        core.update(_serialize_dict(_strip_none(data)))

    def update_llm(self, name: str, config: LLMConfig) -> None:
        llm = self._ensure_section('llm')
        cfg_dict = _serialize_dict(_strip_none(config.model_dump()))
        if name == 'llm':
            # Write into the base [llm] section, but keep existing subsections
            # by only updating non-dict keys.
            for k, v in list(cfg_dict.items()):
                if isinstance(v, dict):
                    # Shouldn't happen from model_dump, but guard anyway
                    continue
                llm[k] = v
        else:
            # Write into [llm.<name>] subsection
            subsection = llm.get(name)
            if not isinstance(subsection, dict):
                subsection = {}
                llm[name] = subsection
            subsection.update(cfg_dict)

    def write(self) -> None:
        os.makedirs(os.path.dirname(self.toml_file) or '.', exist_ok=True)
        with open(self.toml_file, 'w', encoding='utf-8') as f:
            toml.dump(self._data, f)
