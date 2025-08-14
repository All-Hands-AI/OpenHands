from pydantic import SecretStr

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.openhands_config import OpenHandsConfig


def test_set_llm_config_replaces_group():
    cfg = OpenHandsConfig()
    # default exists at key 'llm'
    before = cfg.get_llm_config()
    assert isinstance(before, LLMConfig)

    new_cfg = LLMConfig(
        model='my-model', api_key=SecretStr('secret'), base_url='https://x'
    )
    cfg.set_llm_config(new_cfg, 'llm')

    # Ensure replacement took
    assert cfg.get_llm_config().model == 'my-model'
    assert cfg.get_llm_config().base_url == 'https://x'
    assert cfg.get_llm_config().api_key.get_secret_value() == 'secret'


def test_set_llm_config_creates_named_group_when_missing():
    cfg = OpenHandsConfig()
    assert 'custom' not in cfg.llms

    cfg.set_llm_config(LLMConfig(model='another-model'), 'custom')

    assert 'custom' in cfg.llms
    assert cfg.get_llm_config('custom').model == 'another-model'
