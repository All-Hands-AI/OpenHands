from pathlib import Path

import toml

from openhands.core.config.condenser_config import (
    LLMSummarizingCondenserConfig,
    NoOpCondenserConfig,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_write_condenser_noop(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_condenser(NoOpCondenserConfig())
    writer.write()

    data = toml.load(cfg_path)
    assert 'condenser' in data
    assert data['condenser']['type'] == 'noop'


def test_write_condenser_llm_nested(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    llm = LLMConfig(model='gpt-4o-mini', temperature=0.2)
    cfg = LLMSummarizingCondenserConfig(llm_config=llm, keep_first=2, max_size=50)

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_condenser(cfg)
    writer.write()

    data = toml.load(cfg_path)
    assert data['condenser']['type'] == 'llm'
    assert data['condenser']['llm_config']['model'] == 'gpt-4o-mini'
    assert data['condenser']['keep_first'] == 2


def test_write_condenser_llm_attention_as_dict(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_condenser({'type': 'llm_attention', 'max_size': 10})
    writer.write()

    data = toml.load(cfg_path)
    assert data['condenser']['type'] == 'llm_attention'
    assert data['condenser']['max_size'] == 10


def test_agent_embeds_noop_condenser_and_persists(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    from openhands.core.config.agent_config import AgentConfig

    agent = AgentConfig()
    agent.condenser = NoOpCondenserConfig()

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_agent_base(agent)
    writer.write()

    data = toml.load(cfg_path)
    assert 'agent' in data
    assert 'condenser' in data['agent']
    assert data['agent']['condenser']['type'] == 'noop'
