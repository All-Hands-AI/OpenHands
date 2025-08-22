from pathlib import Path

import toml

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_remove_section_and_subsection(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    w = TOMLConfigWriter(str(cfg_path))
    w.update_llm_base(LLMConfig(model='m'))
    w.update_llm_named('x', LLMConfig(model='m2'))
    w.write()

    # remove llm.x
    w = TOMLConfigWriter(str(cfg_path))
    w.remove_section('llm', 'x')
    w.write()

    data = toml.load(cfg_path)
    assert 'llm' in data
    assert 'x' not in data['llm']

    # remove llm entirely
    w = TOMLConfigWriter(str(cfg_path))
    w.remove_section('llm')
    w.write()
    data = toml.load(cfg_path)
    assert 'llm' not in data
