import os

from pydantic import SecretStr

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.toml_writer import TOMLConfigWriter


def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def test_toml_writer_creates_and_updates_core_and_llm_sections(tmp_path):
    # Use a temp file under pytest's tmp_path
    toml_path = os.path.join(tmp_path, 'config.toml')

    # Initial write with core search_api_key
    writer = TOMLConfigWriter(toml_file=toml_path)
    writer.update_core({'search_api_key': SecretStr('abc')})
    # Ensure a base llm exists
    writer.update_llm('llm', LLMConfig(model='m1', api_key=SecretStr('k1')))
    writer.write()

    data = read_file(toml_path)
    assert '[core]' in data
    assert 'search_api_key = "abc"' in data
    assert '[llm]' in data
    assert 'model = "m1"' in data
    assert 'api_key = "k1"' in data

    # Update named LLM subsection
    writer = TOMLConfigWriter(toml_file=toml_path)
    writer.update_llm('custom', LLMConfig(model='m2', base_url='https://x'))
    writer.write()

    data = read_file(toml_path)
    assert '[llm.custom]' in data
    assert 'model = "m2"' in data
    assert 'base_url = "https://x"' in data
