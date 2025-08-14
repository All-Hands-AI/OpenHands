from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def test_toml_writer_updates_agent_sections(tmp_path):
    toml_path = tmp_path / 'config.toml'

    writer = TOMLConfigWriter(toml_file=str(toml_path))
    base_agent = AgentConfig(enable_browsing=False, enable_editor=False)
    writer.update_agent('agent', base_agent)
    writer.write()

    content = toml_path.read_text(encoding='utf-8')
    assert '[agent]' in content
    assert 'enable_browsing = false' in content
    assert 'enable_editor = false' in content

    # now add a subsection
    writer = TOMLConfigWriter(toml_file=str(toml_path))
    custom = AgentConfig(enable_browsing=True, enable_editor=True)
    writer.update_agent('CodeActAgent', custom)
    writer.write()

    content = toml_path.read_text(encoding='utf-8')
    assert '[agent.CodeActAgent]' in content
    assert 'enable_browsing = true' in content
    assert 'enable_editor = true' in content
