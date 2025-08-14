from __future__ import annotations

import os
from typing import Any

import toml
from pydantic import BaseModel, SecretStr

from openhands.core import logger
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.cli_config import CLIConfig
from openhands.core.config.condenser_config import CondenserConfig
from openhands.core.config.extended_config import ExtendedConfig
from openhands.core.config.kubernetes_config import KubernetesConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _serialize_value(v: Any) -> Any:
    if isinstance(v, SecretStr):
        return v.get_secret_value()
    if isinstance(v, BaseModel):
        return _serialize_dict(v.model_dump(exclude_unset=True, exclude_none=True))
    if isinstance(v, list):
        return [_serialize_value(i) for i in v]
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
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

    def update_agent(self, name: str, config: AgentConfig) -> None:
        agent = self._ensure_section('agent')
        cfg_dict = _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        )
        if name == 'agent':
            for k, v in list(cfg_dict.items()):
                if isinstance(v, dict):
                    continue
                agent[k] = v
        else:
            # Write into [agent.<name>] subsection
            subsection = agent.get(name)
            if not isinstance(subsection, dict):
                subsection = {}
                agent[name] = subsection
            subsection.update(cfg_dict)

    def update_security(self, config: SecurityConfig) -> None:
        sec = self._ensure_section('security')
        sec.update(
            _serialize_dict(
                _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
            )
        )

    def update_sandbox(self, config: SandboxConfig) -> None:
        sb = self._ensure_section('sandbox')
        sb.update(
            _serialize_dict(
                _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
            )
        )

    def update_kubernetes(self, config: KubernetesConfig) -> None:
        k8s = self._ensure_section('kubernetes')
        k8s.update(
            _serialize_dict(
                _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
            )
        )

    def update_cli(self, config: CLIConfig) -> None:
        cli = self._ensure_section('cli')
        cli.update(
            _serialize_dict(
                _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
            )
        )

    def update_extended(self, data: ExtendedConfig | dict[str, Any]) -> None:
        ext = self._ensure_section('extended')
        if isinstance(data, ExtendedConfig):
            payload: dict[str, Any] = data.model_dump()
        else:
            payload = data
        ext.update(_serialize_dict(_strip_none(payload)))

    def update_condenser(self, config: CondenserConfig | dict[str, Any]) -> None:
        cond = self._ensure_section('condenser')
        if isinstance(config, BaseModel):
            # For union models like CondenserConfig, ensure 'type' is persisted even if default
            data = config.model_dump(exclude_none=True)
            if 'type' not in data and hasattr(config, 'type'):
                try:
                    data['type'] = getattr(config, 'type')
                except Exception:
                    pass
        else:
            data = config
        cond.update(_serialize_dict(_strip_none(data)))

    def update_mcp(self, config: MCPConfig) -> None:
        mcp = self._ensure_section('mcp')
        mcp.update(
            _serialize_dict(
                _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
            )
        )

    def write(self) -> None:
        os.makedirs(os.path.dirname(self.toml_file) or '.', exist_ok=True)
        with open(self.toml_file, 'w', encoding='utf-8') as f:
            toml.dump(self._data, f)
