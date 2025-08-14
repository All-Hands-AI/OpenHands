from __future__ import annotations

import os
from typing import Any

import tomlkit as toml
from tomlkit.items import Table
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
        self._doc = None
        self._load()

    def _load(self) -> None:
        try:
            with open(self.toml_file, 'r', encoding='utf-8') as f:
                text = f.read()
                self._doc = toml.parse(text)
        except FileNotFoundError:
            self._doc = toml.document()
        except Exception as e:
            logger.openhands_logger.warning(
                f'Cannot parse existing TOML at {self.toml_file}: {e}. Recreating file.'
            )
            self._doc = toml.document()

    def _ensure_section(self, name: str) -> Table:
        section = self._doc.get(name)
        if not isinstance(section, dict):
            section = toml.table()
            self._doc[name] = section
        return section

    def update_core(self, data: dict[str, Any]) -> None:
        core = self._ensure_section('core')
        core.update(_serialize_dict(_strip_none(data)))

    def update_llm(self, name: str, config: LLMConfig) -> None:
        llm = self._ensure_section('llm')
        cfg_dict = _serialize_dict(_strip_none(config.model_dump()))
        if name == 'llm':
            for k, v in list(cfg_dict.items()):
                if isinstance(v, dict):
                    continue
                # preserve comment if existed
                existing = llm.get(k)
                item = toml.item(v)
                try:
                    if hasattr(existing, 'trivia') and existing.trivia.comment:
                        item.trivia.comment = existing.trivia.comment
                except Exception:
                    pass
                llm[k] = item
        else:
            # Write into [llm.<name>] subsection
            subsection = llm.get(name)
            if not isinstance(subsection, dict):
                subsection = toml.table()
                llm[name] = subsection
            for k, v in cfg_dict.items():
                existing = subsection.get(k)
                item = toml.item(v)
                try:
                    if hasattr(existing, 'trivia') and existing.trivia.comment:
                        item.trivia.comment = existing.trivia.comment
                except Exception:
                    pass
                subsection[k] = item

    def update_agent(self, name: str, config: AgentConfig) -> None:
        agent = self._ensure_section('agent')
        cfg_dict = _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        )
        if name == 'agent':
            for k, v in list(cfg_dict.items()):
                if isinstance(v, dict):
                    continue
                existing = agent.get(k)
                item = toml.item(v)
                try:
                    if hasattr(existing, 'trivia') and existing.trivia.comment:
                        item.trivia.comment = existing.trivia.comment
                except Exception:
                    pass
                agent[k] = item
        else:
            # Write into [agent.<name>] subsection
            subsection = agent.get(name)
            if not isinstance(subsection, dict):
                subsection = toml.table()
                agent[name] = subsection
            for k, v in cfg_dict.items():
                existing = subsection.get(k)
                item = toml.item(v)
                try:
                    if hasattr(existing, 'trivia') and existing.trivia.comment:
                        item.trivia.comment = existing.trivia.comment
                except Exception:
                    pass
                subsection[k] = item

    def update_security(self, config: SecurityConfig) -> None:
        sec = self._ensure_section('security')
        sec.update(
            _serialize_dict(
                _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
            )
        )

    def update_sandbox(self, config: SandboxConfig) -> None:
        sb = self._ensure_section('sandbox')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
        ).items():
            existing = sb.get(k)
            item = toml.item(v)
            try:
                if hasattr(existing, 'trivia') and existing.trivia.comment:
                    item.trivia.comment = existing.trivia.comment
            except Exception:
                pass
            sb[k] = item

    def update_kubernetes(self, config: KubernetesConfig) -> None:
        k8s = self._ensure_section('kubernetes')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
        ).items():
            existing = k8s.get(k)
            item = toml.item(v)
            try:
                if hasattr(existing, 'trivia') and existing.trivia.comment:
                    item.trivia.comment = existing.trivia.comment
            except Exception:
                pass
            k8s[k] = item

    def update_cli(self, config: CLIConfig) -> None:
        cli = self._ensure_section('cli')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
        ).items():
            existing = cli.get(k)
            item = toml.item(v)
            try:
                if hasattr(existing, 'trivia') and existing.trivia.comment:
                    item.trivia.comment = existing.trivia.comment
            except Exception:
                pass
            cli[k] = item

    def update_extended(self, data: ExtendedConfig | dict[str, Any]) -> None:
        ext = self._ensure_section('extended')
        if isinstance(data, ExtendedConfig):
            payload: dict[str, Any] = data.model_dump()
        else:
            payload = data
        for k, v in _serialize_dict(_strip_none(payload)).items():
            existing = ext.get(k)
            item = toml.item(v)
            try:
                if hasattr(existing, 'trivia') and existing.trivia.comment:
                    item.trivia.comment = existing.trivia.comment
            except Exception:
                pass
            ext[k] = item

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
        for k, v in _serialize_dict(_strip_none(data)).items():
            existing = cond.get(k)
            item = toml.item(v)
            try:
                if hasattr(existing, 'trivia') and existing.trivia.comment:
                    item.trivia.comment = existing.trivia.comment
            except Exception:
                pass
            cond[k] = item

    def update_mcp(self, config: MCPConfig) -> None:
        mcp = self._ensure_section('mcp')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_none=True, exclude_unset=True))
        ).items():
            existing = mcp.get(k)
            item = toml.item(v)
            try:
                if hasattr(existing, 'trivia') and existing.trivia.comment:
                    item.trivia.comment = existing.trivia.comment
            except Exception:
                pass
            mcp[k] = item

    def write(self) -> None:
        os.makedirs(os.path.dirname(self.toml_file) or '.', exist_ok=True)
        tmp = f"{self.toml_file}.tmp"
        with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(toml.dumps(self._doc))
        os.replace(tmp, self.toml_file)
