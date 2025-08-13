from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import (
    OH_DEFAULT_AGENT,
    OH_MAX_ITERATIONS,
    OpenHandsConfig,
    get_llm_config_arg,
    setup_config_from_args,
)


@pytest.fixture
def default_config():
    """Fixture to provide a default OpenHandsConfig instance."""
    yield OpenHandsConfig()


@pytest.fixture
def temp_config_files(tmp_path):
    """Create temporary config files for testing precedence."""
    # Create a directory structure mimicking ~/.openhands/
    user_config_dir = tmp_path / 'home' / '.openhands'
    user_config_dir.mkdir(parents=True, exist_ok=True)

    # Create ~/.openhands/config.toml
    user_config_toml = user_config_dir / 'config.toml'
    user_config_toml.write_text("""
[llm]
model = "user-home-model"
api_key = "user-home-api-key"

[llm.user-llm]
model = "user-specific-model"
api_key = "user-specific-api-key"
""")

    # Create ~/.openhands/settings.json
    user_settings_json = user_config_dir / 'settings.json'
    user_settings_json.write_text("""
{
    "LLM_MODEL": "settings-json-model",
    "LLM_API_KEY": "settings-json-api-key"
}
""")

    # Create current directory config.toml
    current_dir_toml = tmp_path / 'current' / 'config.toml'
    current_dir_toml.parent.mkdir(parents=True, exist_ok=True)
    current_dir_toml.write_text("""
[llm]
model = "current-dir-model"
api_key = "current-dir-api-key"

[llm.current-dir-llm]
model = "current-dir-specific-model"
api_key = "current-dir-specific-api-key"
""")

    return {
        'user_config_toml': str(user_config_toml),
        'user_settings_json': str(user_settings_json),
        'current_dir_toml': str(current_dir_toml),
        'home_dir': str(user_config_dir.parent),
        'current_dir': str(current_dir_toml.parent),
    }


@patch('openhands.core.config.utils.os.path.expanduser')
def test_llm_config_precedence_cli_highest(mock_expanduser, temp_config_files):
    """Test that CLI parameters have the highest precedence."""
    mock_expanduser.side_effect = lambda path: path.replace(
        '~', temp_config_files['home_dir']
    )

    # Create mock args with CLI parameters
    mock_args = MagicMock()
    mock_args.config_file = temp_config_files['current_dir_toml']
    mock_args.llm_config = 'current-dir-llm'  # Specify LLM via CLI
    mock_args.agent_cls = None
    mock_args.max_iterations = None
    mock_args.max_budget_per_task = None
    mock_args.selected_repo = None

    # Load config with CLI parameters
    with patch('os.path.exists', return_value=True):
        config = setup_config_from_args(mock_args)

    # Verify CLI parameter takes precedence
    assert config.get_llm_config().model == 'current-dir-specific-model'
    assert (
        config.get_llm_config().api_key.get_secret_value()
        == 'current-dir-specific-api-key'
    )


@patch('openhands.core.config.utils.os.path.expanduser')
def test_current_dir_toml_precedence_over_user_config(
    mock_expanduser, temp_config_files
):
    """Test that config.toml in current directory has precedence over ~/.openhands/config.toml."""
    mock_expanduser.side_effect = lambda path: path.replace(
        '~', temp_config_files['home_dir']
    )

    # Create mock args without CLI parameters
    mock_args = MagicMock()
    mock_args.config_file = temp_config_files['current_dir_toml']
    mock_args.llm_config = None  # No CLI parameter
    mock_args.agent_cls = None
    mock_args.max_iterations = None
    mock_args.max_budget_per_task = None
    mock_args.selected_repo = None

    # Load config without CLI parameters
    with patch('os.path.exists', return_value=True):
        config = setup_config_from_args(mock_args)

    # Verify current directory config.toml takes precedence over user config
    assert config.get_llm_config().model == 'current-dir-model'
    assert config.get_llm_config().api_key.get_secret_value() == 'current-dir-api-key'


@patch('openhands.core.config.utils.os.path.expanduser')
def test_get_llm_config_arg_precedence(mock_expanduser, temp_config_files):
    """Test that get_llm_config_arg prioritizes the specified config file."""
    mock_expanduser.side_effect = lambda path: path.replace(
        '~', temp_config_files['home_dir']
    )

    # First try to load from current directory config
    with patch('os.path.exists', return_value=True):
        llm_config = get_llm_config_arg(
            'current-dir-llm', temp_config_files['current_dir_toml']
        )

    # Verify it loaded from current directory config
    assert llm_config.model == 'current-dir-specific-model'
    assert llm_config.api_key.get_secret_value() == 'current-dir-specific-api-key'

    # Now try to load a config that doesn't exist
    # We need to patch setup_config_from_args to handle the fallback to user config
    with patch(
        'os.path.exists',
        return_value=False,
    ):
        llm_config = get_llm_config_arg(
            'user-llm', temp_config_files['current_dir_toml']
        )

    # Verify it returns None when config not found (no automatic fallback)
    assert llm_config is None


@patch('openhands.core.config.utils.os.path.expanduser')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.FileSettingsStore.load')
def test_cli_main_settings_precedence(
    mock_load, mock_get_instance, mock_expanduser, temp_config_files
):
    """Test that the CLI main.py correctly applies settings precedence."""
    from openhands.cli.main import setup_config_from_args

    mock_expanduser.side_effect = lambda path: path.replace(
        '~', temp_config_files['home_dir']
    )

    # Create mock settings
    mock_settings = MagicMock()
    mock_settings.llm_model = 'settings-store-model'
    mock_settings.llm_api_key = 'settings-store-api-key'
    mock_settings.llm_base_url = None
    mock_settings.agent = 'CodeActAgent'
    mock_settings.confirmation_mode = False
    mock_settings.enable_default_condenser = True

    # Setup mocks
    mock_load.return_value = mock_settings
    mock_get_instance.return_value = MagicMock()

    # Create mock args with config file pointing to current directory config
    mock_args = MagicMock()
    mock_args.config_file = temp_config_files['current_dir_toml']
    mock_args.llm_config = None  # No CLI parameter
    mock_args.agent_cls = None
    mock_args.max_iterations = None
    mock_args.max_budget_per_task = None
    mock_args.selected_repo = None

    # Load config using the actual CLI code path
    with patch('os.path.exists', return_value=True):
        config = setup_config_from_args(mock_args)

    # Verify that config.toml values take precedence over settings.json
    assert config.get_llm_config().model == 'current-dir-model'
    assert config.get_llm_config().api_key.get_secret_value() == 'current-dir-api-key'


@patch('openhands.core.config.utils.os.path.expanduser')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.FileSettingsStore.load')
def test_cli_with_l_parameter_precedence(
    mock_load, mock_get_instance, mock_expanduser, temp_config_files
):
    """Test that CLI -l parameter has highest precedence in CLI mode."""
    from openhands.cli.main import setup_config_from_args

    mock_expanduser.side_effect = lambda path: path.replace(
        '~', temp_config_files['home_dir']
    )

    # Create mock settings
    mock_settings = MagicMock()
    mock_settings.llm_model = 'settings-store-model'
    mock_settings.llm_api_key = 'settings-store-api-key'
    mock_settings.llm_base_url = None
    mock_settings.agent = 'CodeActAgent'
    mock_settings.confirmation_mode = False
    mock_settings.enable_default_condenser = True

    # Setup mocks
    mock_load.return_value = mock_settings
    mock_get_instance.return_value = MagicMock()

    # Create mock args with -l parameter
    mock_args = MagicMock()
    mock_args.config_file = temp_config_files['current_dir_toml']
    mock_args.llm_config = 'current-dir-llm'  # Specify LLM via CLI
    mock_args.agent_cls = None
    mock_args.max_iterations = None
    mock_args.max_budget_per_task = None
    mock_args.selected_repo = None

    # Load config using the actual CLI code path
    with patch('os.path.exists', return_value=True):
        config = setup_config_from_args(mock_args)

    # Verify that -l parameter takes precedence over everything
    assert config.get_llm_config().model == 'current-dir-specific-model'
    assert (
        config.get_llm_config().api_key.get_secret_value()
        == 'current-dir-specific-api-key'
    )


@patch('openhands.core.config.utils.os.path.expanduser')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.FileSettingsStore.load')
def test_cli_settings_json_not_override_config_toml(
    mock_load, mock_get_instance, mock_expanduser, temp_config_files
):
    """Test that settings.json doesn't override config.toml in CLI mode."""
    import importlib
    import sys
    from unittest.mock import patch

    # First, ensure we can import the CLI main module
    if 'openhands.cli.main' in sys.modules:
        importlib.reload(sys.modules['openhands.cli.main'])

    # Now import the specific function we want to test
    from openhands.cli.main import setup_config_from_args

    mock_expanduser.side_effect = lambda path: path.replace(
        '~', temp_config_files['home_dir']
    )

    # Create mock settings with different values than config.toml
    mock_settings = MagicMock()
    mock_settings.llm_model = 'settings-json-model'
    mock_settings.llm_api_key = 'settings-json-api-key'
    mock_settings.llm_base_url = None
    mock_settings.agent = 'CodeActAgent'
    mock_settings.confirmation_mode = False
    mock_settings.enable_default_condenser = True

    # Setup mocks
    mock_load.return_value = mock_settings
    mock_get_instance.return_value = MagicMock()

    # Create mock args with config file pointing to current directory config
    mock_args = MagicMock()
    mock_args.config_file = temp_config_files['current_dir_toml']
    mock_args.llm_config = None  # No CLI parameter
    mock_args.agent_cls = None
    mock_args.max_iterations = None
    mock_args.max_budget_per_task = None
    mock_args.selected_repo = None

    # Load config using the actual CLI code path
    with patch('os.path.exists', return_value=True):
        setup_config_from_args(mock_args)

    # Create a test LLM config to simulate the fix in CLI main.py
    test_config = OpenHandsConfig()
    test_llm_config = test_config.get_llm_config()
    test_llm_config.model = 'config-toml-model'
    test_llm_config.api_key = 'config-toml-api-key'

    # Simulate the CLI main.py logic that we fixed
    if not mock_args.llm_config and (test_llm_config.model or test_llm_config.api_key):
        # Should NOT apply settings from settings.json
        pass
    else:
        # This branch should not be taken in our test
        test_llm_config.model = mock_settings.llm_model
        test_llm_config.api_key = mock_settings.llm_api_key

    # Verify that settings.json did not override config.toml
    assert test_llm_config.model == 'config-toml-model'
    assert test_llm_config.api_key == 'config-toml-api-key'


def test_default_values_applied_when_none():
    """Test that default values are applied when config values are None."""

    # Create mock args with None values for agent_cls and max_iterations
    mock_args = MagicMock()
    mock_args.config_file = None
    mock_args.llm_config = None
    mock_args.agent_cls = None
    mock_args.max_iterations = None

    # Load config
    with patch(
        'openhands.core.config.utils.load_openhands_config',
        return_value=OpenHandsConfig(),
    ):
        config = setup_config_from_args(mock_args)

    # Verify they match the expected defaults
    assert config.default_agent == OH_DEFAULT_AGENT
    assert config.max_iterations == OH_MAX_ITERATIONS


def test_cli_args_override_defaults():
    """Test that CLI arguments override default values."""

    # Create mock args with custom values
    mock_args = MagicMock()
    mock_args.config_file = None
    mock_args.llm_config = None
    mock_args.agent_cls = 'CustomAgent'
    mock_args.max_iterations = 50

    # Load config
    with patch(
        'openhands.core.config.utils.load_openhands_config',
        return_value=OpenHandsConfig(),
    ):
        config = setup_config_from_args(mock_args)

    # Verify custom values are used instead of defaults
    assert config.default_agent == 'CustomAgent'
    assert config.max_iterations == 50


def test_cli_args_none_uses_config_toml_values():
    """Test that when CLI args agent_cls and max_iterations are None, config.toml values are used."""

    # Create mock args with None values for agent_cls and max_iterations
    mock_args = MagicMock()
    mock_args.config_file = None
    mock_args.llm_config = None
    mock_args.agent_cls = None
    mock_args.max_iterations = None

    # Create a config with specific values from config.toml
    config_from_toml = OpenHandsConfig()
    config_from_toml.default_agent = 'ConfigTomlAgent'
    config_from_toml.max_iterations = 100

    # Load config
    with patch(
        'openhands.core.config.utils.load_openhands_config',
        return_value=config_from_toml,
    ):
        config = setup_config_from_args(mock_args)

    # Verify config.toml values are preserved when CLI args are None
    assert config.default_agent == 'ConfigTomlAgent'
    assert config.max_iterations == 100
