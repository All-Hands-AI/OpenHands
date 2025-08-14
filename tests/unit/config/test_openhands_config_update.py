from pydantic import SecretStr

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.openhands_config import OpenHandsConfig


def test_update_llm_config_updates_only_non_none_fields():
    cfg = OpenHandsConfig()
    # default exists at key 'llm'
    before = cfg.get_llm_config()
    assert isinstance(before, LLMConfig)

    updated = cfg.update_llm_config(
        'llm', model='my-model', api_key=SecretStr('secret'), base_url='https://x'
    )

    # Ensure same object type and values updated
    assert isinstance(updated, LLMConfig)
    assert cfg.get_llm_config().model == 'my-model'
    assert cfg.get_llm_config().base_url == 'https://x'
    assert cfg.get_llm_config().api_key.get_secret_value() == 'secret'

    # Unspecified fields remain unchanged (default temperature is 0.0)
    assert cfg.get_llm_config().temperature == before.temperature


def test_update_llm_config_creates_named_group_when_missing():
    cfg = OpenHandsConfig()
    assert 'custom' not in cfg.llms

    updated = cfg.update_llm_config('custom', model='another-model')

    assert 'custom' in cfg.llms
    assert updated.model == 'another-model'
    assert cfg.get_llm_config('custom').model == 'another-model'
