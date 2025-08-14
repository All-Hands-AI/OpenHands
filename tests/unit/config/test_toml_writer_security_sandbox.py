import toml
from pathlib import Path

from openhands.core.config.security_config import SecurityConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_write_security_and_sandbox(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_security(SecurityConfig())
    writer.update_sandbox(SandboxConfig())
    writer.write()

    data = toml.load(cfg_path)
    assert 'security' in data
    assert isinstance(data['security'], dict)
    assert 'sandbox' in data
    assert isinstance(data['sandbox'], dict)
