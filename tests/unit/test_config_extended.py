import pytest

from openhands.core.config.extended_config import ExtendedConfig


def test_extended_config_from_dict():
    """
    Test that ExtendedConfig.from_dict successfully creates an instance
    from a dictionary containing arbitrary extra keys.
    """
    data = {'foo': 'bar', 'baz': 123, 'flag': True}
    ext_cfg = ExtendedConfig.from_dict(data)

    # Check that the keys are accessible both as attributes and via __getitem__
    assert ext_cfg.foo == 'bar'
    assert ext_cfg['baz'] == 123
    assert ext_cfg.flag is True


def test_extended_config_str_and_repr():
    """
    Test that __str__ and __repr__ return the correct string representations
    of the ExtendedConfig instance.
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
    """
    Test that __getitem__ and __getattr__ can be used to access values
    in the ExtendedConfig instance.
    """
    data = {'key1': 'value1', 'key2': 2}
    ext_cfg = ExtendedConfig.from_dict(data)

    # Attribute access
    assert ext_cfg.key1 == 'value1'
    # Dictionary-style access
    assert ext_cfg['key2'] == 2


def test_extended_config_invalid_key():
    """
    Test that accessing a non-existent key via attribute access raises AttributeError.
    """
    data = {'existing': 'yes'}
    ext_cfg = ExtendedConfig.from_dict(data)

    with pytest.raises(AttributeError):
        _ = ext_cfg.nonexistent
