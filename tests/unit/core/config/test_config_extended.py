import os

import pytest

from openhands.core.config.extended_config import ExtendedConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.config.utils import load_from_toml


def test_extended_config_from_dict():
    """Test that ExtendedConfig.from_dict successfully creates an instance.

    This test verifies that the from_dict method correctly creates an instance
    from a dictionary containing arbitrary extra keys.
    """
    data = {'foo': 'bar', 'baz': 123, 'flag': True}
    ext_cfg = ExtendedConfig.from_dict(data)

    # Check that the keys are accessible both as attributes and via __getitem__
    assert ext_cfg.foo == 'bar'
    assert ext_cfg['baz'] == 123
    assert ext_cfg.flag is True
    # Verify the root dictionary contains all keys
    assert ext_cfg.root == data


def test_extended_config_empty():
    """Test that an empty ExtendedConfig can be created and accessed."""
    ext_cfg = ExtendedConfig.from_dict({})
    assert ext_cfg.root == {}

    # Creating directly should also work
    ext_cfg2 = ExtendedConfig({})
    assert ext_cfg2.root == {}


def test_extended_config_str_and_repr():
    """Test that __str__ and __repr__ return the correct string representations.

    This test verifies that the string representations of the ExtendedConfig instance
    include the expected key/value pairs.
    """
    data = {'alpha': 'test', 'beta': 42}
    ext_cfg = ExtendedConfig.from_dict(data)
    string_repr = str(ext_cfg)
    repr_str = repr(ext_cfg)

    # Ensure the representations include our key/value pairs
    assert "alpha='test'" in string_repr
    assert 'beta=42' in string_repr

    # __repr__ should match __str__
    assert string_repr == repr_str


def test_extended_config_getitem_and_getattr():
    """Test that __getitem__ and __getattr__ can be used to access values.

    This test verifies that values in the ExtendedConfig instance can be accessed
    both via attribute access and dictionary-style access.
    """
    data = {'key1': 'value1', 'key2': 2}
    ext_cfg = ExtendedConfig.from_dict(data)

    # Attribute access
    assert ext_cfg.key1 == 'value1'
    # Dictionary-style access
    assert ext_cfg['key2'] == 2


def test_extended_config_invalid_key():
    """Test that accessing a non-existent key via attribute access raises AttributeError."""
    data = {'existing': 'yes'}
    ext_cfg = ExtendedConfig.from_dict(data)

    with pytest.raises(AttributeError):
        _ = ext_cfg.nonexistent

    with pytest.raises(KeyError):
        _ = ext_cfg['nonexistent']


def test_app_config_extended_from_toml(tmp_path: os.PathLike) -> None:
    """Test that the [extended] section in a TOML file is correctly loaded.

    This test verifies that the [extended] section is loaded into OpenHandsConfig.extended
    and that it accepts arbitrary keys.
    """
    # Create a temporary TOML file with multiple sections including [extended]
    config_content = """
[core]
workspace_base = "/tmp/workspace"

[llm]
model = "test-model"
api_key = "toml-api-key"

[extended]
custom1 = "custom_value"
custom2 = 42
llm = "overridden"  # even a key like 'llm' is accepted in extended

[agent]
enable_prompt_extensions = true
"""
    config_file = tmp_path / 'config.toml'
    config_file.write_text(config_content)

    # Load the TOML into the OpenHandsConfig instance
    config = OpenHandsConfig()
    load_from_toml(config, str(config_file))

    # Verify that extended section is applied
    assert config.extended.custom1 == 'custom_value'
    assert config.extended.custom2 == 42
    # Even though 'llm' is defined in extended, it should not affect the main llm config.
    assert config.get_llm_config().model == 'test-model'


def test_app_config_extended_default(tmp_path: os.PathLike) -> None:
    """Test default behavior when no [extended] section exists.

    This test verifies that if there is no [extended] section in the TOML file,
    OpenHandsConfig.extended remains its default (empty) ExtendedConfig.
    """
    config_content = """
[core]
workspace_base = "/tmp/workspace"

[llm]
model = "test-model"
api_key = "toml-api-key"

[agent]
enable_prompt_extensions = true
"""
    config_file = tmp_path / 'config.toml'
    config_file.write_text(config_content)

    config = OpenHandsConfig()
    load_from_toml(config, str(config_file))

    # Extended config should be empty
    assert config.extended.root == {}


def test_app_config_extended_random_keys(tmp_path: os.PathLike) -> None:
    """Test that the extended section accepts arbitrary keys.

    This test verifies that the extended section accepts arbitrary keys,
    including ones not defined in any schema.
    """
    config_content = """
[core]
workspace_base = "/tmp/workspace"

[extended]
random_key = "random_value"
another_key = 3.14
"""
    config_file = tmp_path / 'config.toml'
    config_file.write_text(config_content)

    config = OpenHandsConfig()
    load_from_toml(config, str(config_file))

    # Verify that extended config holds the arbitrary keys with correct values.
    assert config.extended.random_key == 'random_value'
    assert config.extended.another_key == 3.14
    # Verify the root dictionary contains all keys
    assert config.extended.root == {'random_key': 'random_value', 'another_key': 3.14}
