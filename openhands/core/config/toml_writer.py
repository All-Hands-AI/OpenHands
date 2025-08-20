from __future__ import annotations

import os
import time
from tempfile import NamedTemporaryFile
from typing import Any

import tomlkit
from pydantic import BaseModel, SecretStr

from openhands.core import logger
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.cli_config import CLIConfig
from openhands.core.config.condenser_config import CondenserConfig
from openhands.core.config.extended_config import ExtendedConfig
from openhands.core.config.kubernetes_config import KubernetesConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _model_dump_including_type(m: BaseModel) -> dict[str, Any]:
    data = m.model_dump(exclude_unset=True, exclude_none=True)
    # Ensure union-discriminator-like 'type' is preserved
    if 'type' not in data and hasattr(m, 'type'):
        try:
            data['type'] = getattr(m, 'type')
        except Exception:
            pass
    return data


def _serialize_value(v: Any) -> Any:
    if isinstance(v, SecretStr):
        return v.get_secret_value()
    if isinstance(v, BaseModel):
        return _serialize_dict(_model_dump_including_type(v))
    if isinstance(v, list):
        return [_serialize_value(i) for i in v]
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    return v


def _serialize_dict(d: dict[str, Any]) -> dict[str, Any]:
    return {k: _serialize_value(v) for k, v in d.items()}


class _SimpleFileLock:
    def __init__(self, path: str, timeout: float = 5.0, poll_interval: float = 0.1):
        self.lock_path = path + '.lock'
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._acquired = False

    def __enter__(self):
        start = time.time()
        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode('utf-8'))
                os.close(fd)
                self._acquired = True
                return self
            except FileExistsError:
                if time.time() - start > self.timeout:
                    raise TimeoutError(
                        f'Could not acquire config lock at {self.lock_path}'
                    )
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc, tb):
        if self._acquired:
            try:
                os.unlink(self.lock_path)
            except FileNotFoundError:
                pass


class TOMLConfigWriter:
    """TOML writer for OpenHands config using tomlkit.

    - Preserves comments/formatting when updating
    - Merges keys without clobbering unrelated sections
    - Provides explicit APIs for base vs named subsections
    - Uses atomic write with a simple file lock
    """

    def __init__(self, toml_file: str = 'config.toml') -> None:
        self.toml_file = toml_file
        self._doc = tomlkit.document()
        self._load()

    def _load(self) -> None:
        try:
            with open(self.toml_file, 'r', encoding='utf-8') as f:
                self._doc = tomlkit.parse(f.read())
        except FileNotFoundError:
            self._doc = tomlkit.document()
        except Exception as e:
            logger.openhands_logger.warning(
                f'Cannot parse existing TOML at {self.toml_file}: {e}. Recreating file.'
            )
            self._doc = tomlkit.document()

    def _ensure_table(self, name: str):
        if name not in self._doc or not isinstance(
            self._doc.get(name), tomlkit.items.Table
        ):
            self._doc[name] = tomlkit.table()
        return self._doc[name]

    def update_core(self, data: dict[str, Any]) -> None:
        core_table = self._ensure_table('core')
        allowed = set(OpenHandsConfig.model_fields.keys())
        for k, v in _serialize_dict(_strip_none(data)).items():
            if k not in allowed:
                logger.openhands_logger.warning(
                    f'Unknown config key "{k}" in [core] section; skipping'
                )
                continue
            core_table[k] = v

    # LLM explicit APIs
    def update_llm_base(self, config: LLMConfig) -> None:
        llm_table = self._ensure_table('llm')
        cfg_dict = _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        )
        for k, v in cfg_dict.items():
            # only non-dict scalars in base
            if isinstance(v, dict):
                continue
            llm_table[k] = v

    def update_llm_named(self, name: str, config: LLMConfig) -> None:
        llm_table = self._ensure_table('llm')
        if name == 'llm':
            raise ValueError("Named LLM cannot be 'llm'; use update_llm_base instead")
        sub = llm_table.get(name)
        if not isinstance(sub, tomlkit.items.Table):
            sub = tomlkit.table()
            llm_table[name] = sub
        cfg_dict = _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        )
        for k, v in cfg_dict.items():
            sub[k] = v

    # Agent explicit APIs
    def update_agent_base(self, config: AgentConfig) -> None:
        agent_table = self._ensure_table('agent')
        cfg_dict = _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        )
        for k, v in cfg_dict.items():
            if isinstance(v, dict):
                # nested tables are fine under base agent (e.g., condenser)
                agent_table[k] = v
            else:
                agent_table[k] = v

    def update_agent_named(self, name: str, config: AgentConfig) -> None:
        agent_table = self._ensure_table('agent')
        if name == 'agent':
            raise ValueError(
                "Named agent cannot be 'agent'; use update_agent_base instead"
            )
        sub = agent_table.get(name)
        if not isinstance(sub, tomlkit.items.Table):
            sub = tomlkit.table()
            agent_table[name] = sub
        cfg_dict = _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        )
        for k, v in cfg_dict.items():
            sub[k] = v

    def update_security(self, config: SecurityConfig) -> None:
        sec = self._ensure_table('security')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        ).items():
            sec[k] = v

    def update_sandbox(self, config: SandboxConfig) -> None:
        sb = self._ensure_table('sandbox')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        ).items():
            sb[k] = v

    def update_kubernetes(self, config: KubernetesConfig) -> None:
        k8s = self._ensure_table('kubernetes')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        ).items():
            k8s[k] = v

    def update_cli(self, config: CLIConfig) -> None:
        cli = self._ensure_table('cli')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        ).items():
            cli[k] = v

    def update_extended(self, data: ExtendedConfig | dict[str, Any]) -> None:
        ext = self._ensure_table('extended')
        if isinstance(data, ExtendedConfig):
            payload: dict[str, Any] = data.model_dump(
                exclude_unset=True, exclude_none=True
            )
        else:
            payload = data
        for k, v in _serialize_dict(_strip_none(payload)).items():
            ext[k] = v

    def update_condenser(self, config: CondenserConfig | dict[str, Any]) -> None:
        cond = self._ensure_table('condenser')
        if isinstance(config, BaseModel):
            data = _model_dump_including_type(config)
        else:
            data = config
        for k, v in _serialize_dict(_strip_none(data)).items():
            cond[k] = v

    def update_mcp(self, config: MCPConfig) -> None:
        mcp = self._ensure_table('mcp')
        for k, v in _serialize_dict(
            _strip_none(config.model_dump(exclude_unset=True, exclude_none=True))
        ).items():
            mcp[k] = v

    def remove_section(self, section: str, name: str | None = None) -> None:
        if name is None:
            if section in self._doc:
                del self._doc[section]
            return
        # remove subsection
        tbl = self._doc.get(section)
        if isinstance(tbl, tomlkit.items.Table) and name in tbl:
            del tbl[name]

    def write(self) -> None:
        os.makedirs(os.path.dirname(self.toml_file) or '.', exist_ok=True)
        with _SimpleFileLock(self.toml_file):
            # atomic write
            dir_name = os.path.dirname(self.toml_file) or '.'
            with NamedTemporaryFile(
                'w', encoding='utf-8', dir=dir_name, delete=False
            ) as tmp:
                tmp.write(tomlkit.dumps(self._doc))
                tmp.flush()
                os.fsync(tmp.fileno())
                temp_path = tmp.name
            os.replace(temp_path, self.toml_file)
