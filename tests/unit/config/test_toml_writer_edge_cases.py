from pathlib import Path

import toml

from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.condenser_config import (
    LLMSummarizingCondenserConfig,
    NoOpCondenserConfig,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.config.toml_writer import TOMLConfigWriter
from openhands.core.config.utils import load_from_toml


def test_top_level_condenser_does_not_override_agent_condenser(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    # Write agent with explicit condenser first
    agent = AgentConfig()
    agent.condenser = NoOpCondenserConfig()
    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_agent_base(agent)
    # Also add a top-level condenser of a different type
    writer.update_condenser(LLMSummarizingCondenserConfig(llm_config=LLMConfig()))
    writer.write()

    # Load and ensure agent-level wins
    cfg = OpenHandsConfig()
    load_from_toml(cfg, str(cfg_path))
    loaded = cfg.get_agent_config()
    assert loaded.condenser.type == 'noop', (
        'top-level condenser should not override agent.condenser'
    )


def test_no_default_condenser_injection_when_agent_condenser_present(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    # Only agent.condenser provided; no [condenser] section
    agent = AgentConfig()
    agent.condenser = NoOpCondenserConfig()
    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_agent_base(agent)
    writer.write()

    # Disable/enable flag should not matter; agent already has condenser
    cfg = OpenHandsConfig()
    cfg.enable_default_condenser = True
    load_from_toml(cfg, str(cfg_path))
    assert cfg.get_agent_config().condenser.type == 'noop'


def test_enable_default_condenser_injection_when_absent(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    # No explicit condenser sections written
    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_core({'debug': False})
    writer.write()

    # When enabled and absent, inject LLM summarizing condenser
    cfg = OpenHandsConfig()
    cfg.enable_default_condenser = True
    load_from_toml(cfg, str(cfg_path))
    assert cfg.get_agent_config().condenser.type == 'llm'


def test_disable_default_condenser_and_no_sections_keeps_conversation_window(
    tmp_path: Path,
):
    cfg_path = tmp_path / 'config.toml'

    # No explicit condenser sections written
    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_core({'debug': False})
    writer.write()

    # When disabled, we expect not to inject LLM summarizing condenser (default remains conversation_window)
    cfg = OpenHandsConfig()
    cfg.enable_default_condenser = False
    load_from_toml(cfg, str(cfg_path))
    assert cfg.get_agent_config().condenser.type == 'conversation_window'


def test_named_agent_with_nested_condenser_roundtrip(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    # Write named llm as reference target
    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_llm_base(LLMConfig(model='gpt-4o-mini'))
    writer.update_llm_named('fast', LLMConfig(model='gpt-4o-mini', temperature=0.25))

    # Create named agent with a nested LLM condenser referencing named llm by value (object)
    agent_named = AgentConfig()
    agent_named.condenser = LLMSummarizingCondenserConfig(
        llm_config=LLMConfig(model='gpt-4o-mini', temperature=0.25),
        keep_first=3,
        max_size=77,
    )
    writer.update_agent_named('CodeActAgent', agent_named)
    writer.write()

    # Validate written TOML structure
    data = toml.load(cfg_path)
    assert 'agent' in data and 'CodeActAgent' in data['agent']
    assert data['agent']['CodeActAgent']['condenser']['type'] == 'llm'
    assert data['agent']['CodeActAgent']['condenser']['llm_config']['model']

    # Load back and ensure values preserved
    cfg = OpenHandsConfig()
    load_from_toml(cfg, str(cfg_path))
    named = cfg.get_agent_config('CodeActAgent')
    assert named.condenser.type == 'llm'
    assert getattr(named.condenser, 'keep_first', None) == 3
    assert getattr(named.condenser, 'max_size', None) == 77


def test_top_level_condenser_llm_reference_and_invalid_type_fallback(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_llm_base(LLMConfig(model='gpt-4o-mini'))
    writer.update_llm_named('fast', LLMConfig(model='gpt-4o-mini', temperature=0.33))
    # Write top-level condenser referring to named llm by string and ensure it resolves
    writer.update_condenser({'type': 'llm', 'llm_config': 'fast', 'keep_first': 2})
    writer.write()

    cfg = OpenHandsConfig()
    load_from_toml(cfg, str(cfg_path))
    c = cfg.get_agent_config().condenser
    assert c.type == 'llm'
    # temperature should reflect the named reference
    assert getattr(c.llm_config, 'temperature', None) == 0.33

    # Now corrupt type and ensure fallback to NoOp without blowing up
    data = toml.load(cfg_path)
    data['condenser']['type'] = 'unknown_type'
    cfg_path.write_text(toml.dumps(data), encoding='utf-8')

    cfg2 = OpenHandsConfig()
    load_from_toml(cfg2, str(cfg_path))
    assert cfg2.get_agent_config().condenser.type in {'noop', 'conversation_window'}


def test_agent_extended_dict_is_treated_as_base_field_not_subsection(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    # Agent base with extended dict
    agent = AgentConfig()
    agent.extended = agent.extended.from_dict({'foo': 'bar', 'nested': {'x': 1}})

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_agent_base(agent)
    writer.write()

    data = toml.load(cfg_path)
    assert 'agent' in data
    assert 'extended' in data['agent'] and isinstance(data['agent']['extended'], dict)
    assert data['agent']['extended']['foo'] == 'bar'


def test_top_level_condenser_missing_named_llm_uses_base_llm(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    # Base llm with recognizable temperature
    writer.update_llm_base(LLMConfig(model='gpt-4o-mini', temperature=0.11))
    # Refer to a missing named llm
    writer.update_condenser({'type': 'llm', 'llm_config': 'missing'})
    writer.write()

    cfg = OpenHandsConfig()
    load_from_toml(cfg, str(cfg_path))
    c = cfg.get_agent_config().condenser
    # Should still be llm condenser using the base llm if available
    assert c.type == 'llm'
    assert getattr(c.llm_config, 'temperature', None) == 0.11


def test_named_agent_extended_written_and_loaded(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(str(cfg_path))
    agent_named = AgentConfig()
    agent_named.extended = agent_named.extended.from_dict({'feature': True})
    writer.update_agent_named('MyAgent', agent_named)
    writer.write()

    data = toml.load(cfg_path)
    assert 'agent' in data and 'MyAgent' in data['agent']
    assert data['agent']['MyAgent']['extended']['feature'] is True

    cfg = OpenHandsConfig()
    load_from_toml(cfg, str(cfg_path))
    named = cfg.get_agent_config('MyAgent')
    assert isinstance(named.extended, type(agent_named.extended))
    assert named.extended['feature'] is True
