import toml
from pathlib import Path

from openhands.core.config.cli_config import CLIConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_write_cli(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_cli(CLIConfig(vi_mode=True))
    writer.write()

    data = toml.load(cfg_path)
    assert 'cli' in data
    assert data['cli']['vi_mode'] is True
