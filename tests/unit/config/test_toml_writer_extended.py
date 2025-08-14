from pathlib import Path

import toml

from openhands.core.config.extended_config import ExtendedConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_write_extended_dict(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_extended({'foo': 'bar', 'nested': {'a': 1}})
    writer.write()

    data = toml.load(cfg_path)
    assert 'extended' in data
    assert data['extended']['foo'] == 'bar'
    assert data['extended']['nested']['a'] == 1


def test_write_extended_model(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    ext = ExtendedConfig.from_dict({'x': 42})
    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_extended(ext)
    writer.write()

    data = toml.load(cfg_path)
    assert 'extended' in data
    assert data['extended']['x'] == 42
