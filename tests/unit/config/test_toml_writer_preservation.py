from pathlib import Path

import toml

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.toml_writer import TOMLConfigWriter

EXISTING = """
# Global configuration for OpenHands
[core]
# Keep comments
debug = false

[llm]
# base llm section
model = "claude-sonnet-4-20250514"

[llm.existing]
model = "gpt-4o-mini"
# end
"""


def test_preserve_unrelated_sections_and_comments(tmp_path: Path):
    cfg_path = tmp_path / 'config.toml'
    cfg_path.write_text(EXISTING, encoding='utf-8')

    writer = TOMLConfigWriter(str(cfg_path))
    writer.update_llm_named('newone', LLMConfig(model='o4-mini'))
    writer.write()

    # Ensure both sections survive and comments exist
    txt = cfg_path.read_text(encoding='utf-8')
    assert '# Global configuration for OpenHands' in txt
    assert '# base llm section' in txt
    assert '[llm.existing]' in txt
    assert '[llm.newone]' in txt

    data = toml.load(cfg_path)
    assert 'existing' in data['llm']
    assert 'newone' in data['llm']
