from pathlib import Path
from unittest import mock

import pytest
import tomlkit

# Assuming AppConfig and other necessary classes/functions are importable
# Adjust imports based on actual project structure if needed
from openhands.core.config.app_config import AppConfig
from openhands.core.config.config_save import save_setting_to_user_toml
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import (
    load_app_config,
)

# Mock USER_CONFIG_PATH before it's used at module level if necessary,
# or ensure tests mock it appropriately using fixtures like tmp_path.


# Fixture to provide a clean AppConfig instance for tests
@pytest.fixture
def base_app_config():
    return AppConfig()


# Fixture to provide a clean snapshot (can be modified per test)
@pytest.fixture
def base_snapshot(base_app_config):
    # In a real scenario, this would be populated after loading TOMLs
    # For testing save logic, we often set specific states
    return base_app_config.model_copy(deep=True)


# Fixture to mock Path.home() to use tmp_path
@pytest.fixture(autouse=True)
def mock_home_dir(tmp_path, monkeypatch):
    """Ensure USER_CONFIG_DIR/PATH point to tmp_path for test isolation."""
    mock_home = tmp_path / 'mock_home'
    mock_user_config_dir = mock_home / '.openhands'
    mock_user_config_path = mock_user_config_dir / 'config.toml'

    monkeypatch.setattr(Path, 'home', lambda: mock_home)
    # Important: Patch the constants directly where they are defined or used
    monkeypatch.setattr(
        'openhands.core.config.utils.USER_CONFIG_DIR', mock_user_config_dir
    )
    monkeypatch.setattr(
        'openhands.core.config.utils.USER_CONFIG_PATH', mock_user_config_path
    )
    monkeypatch.setattr(
        'openhands.core.config.config_save.USER_CONFIG_DIR', mock_user_config_dir
    )
    monkeypatch.setattr(
        'openhands.core.config.config_save.USER_CONFIG_PATH', mock_user_config_path
    )

    # Ensure the mocked directory exists for tests that write
    # mock_user_config_dir.mkdir(parents=True, exist_ok=True) # Let the save function create it

    return mock_user_config_path  # Return the path for convenience


# =============================================
# Tests for save_setting_to_user_toml
# =============================================


def test_save_simple_value_success(mock_home_dir, base_app_config, base_snapshot):
    """Test saving a basic value that should be persisted."""
    # Arrange
    user_toml_path = mock_home_dir
    setting_path = 'llm.model'
    new_value = 'new-model-123'
    expected_toml_content = f'[llm]\nmodel = "{new_value}"\n'

    # Ensure runtime and snapshot values allow saving
    # Let's assume the default model is different
    base_app_config.llm.model = 'old-model'  # Simulate current runtime value from TOML
    base_snapshot.llm.model = 'old-model'  # Simulate snapshot value from TOML
    base_app_config.set_toml_snapshot(base_snapshot)  # Set the snapshot

    # Act
    saved = save_setting_to_user_toml(base_app_config, setting_path, new_value)

    # Assert
    assert saved is True
    assert user_toml_path.exists()
    content = user_toml_path.read_text()
    assert content == expected_toml_content


def test_save_value_matches_runtime_no_change(
    mock_home_dir, base_app_config, base_snapshot
):
    """Test that saving is skipped if the new value matches the current runtime value."""
    # Arrange
    user_toml_path = mock_home_dir
    setting_path = 'llm.model'
    current_value = 'current-model-456'
    new_value = current_value  # Same as runtime

    base_app_config.llm.model = current_value
    base_snapshot.llm.model = 'snapshot-model'  # Snapshot differs, but shouldn't matter
    base_app_config.set_toml_snapshot(base_snapshot)

    # Act
    saved = save_setting_to_user_toml(base_app_config, setting_path, new_value)

    # Assert
    assert saved is False
    assert not user_toml_path.exists()  # File shouldn't be created if no change


def test_save_value_overridden_by_env_cli(
    mock_home_dir, base_app_config, base_snapshot
):
    """Test that saving is skipped if the runtime value was overridden by env/cli."""
    # Arrange
    user_toml_path = mock_home_dir
    setting_path = 'llm.model'
    new_value = 'user-wants-this'
    runtime_value = 'env-or-cli-set-this'
    snapshot_value = 'toml-value'  # Different from runtime

    base_app_config.llm.model = runtime_value  # Simulate override
    base_snapshot.llm.model = snapshot_value
    base_app_config.set_toml_snapshot(base_snapshot)

    # Act
    saved = save_setting_to_user_toml(base_app_config, setting_path, new_value)

    # Assert
    assert saved is False
    assert not user_toml_path.exists()  # File shouldn't be created


def test_save_value_set_to_default_removes_key(
    mock_home_dir, base_app_config, base_snapshot
):
    """Test that setting a value back to its default removes it from the user TOML."""
    # Arrange
    user_toml_path = mock_home_dir
    setting_path = 'llm.temperature'
    # Assume default temperature is 0.0 from LLMConfig definition
    default_value = LLMConfig().temperature
    new_value = default_value

    # Pre-populate user TOML with a non-default value
    initial_toml_content = '[llm]\ntemperature = 0.7\n'
    user_toml_path.parent.mkdir(parents=True, exist_ok=True)
    user_toml_path.write_text(initial_toml_content)

    # Set runtime and snapshot to reflect the non-default value initially
    base_app_config.llm.temperature = 0.7
    base_snapshot.llm.temperature = 0.7
    base_app_config.set_toml_snapshot(base_snapshot)

    # Act
    saved = save_setting_to_user_toml(base_app_config, setting_path, new_value)

    # Assert
    assert saved is True
    assert user_toml_path.exists()
    content = user_toml_path.read_text()
    # The key should be removed, leaving an empty or non-existent [llm] section
    # tomlkit might leave the section header if other keys exist, or remove it if empty.
    # Let's check if the specific key is gone.
    doc = tomlkit.parse(content)
    assert 'llm' not in doc or 'temperature' not in doc['llm']


def test_save_nested_value_creates_tables(
    mock_home_dir, base_app_config, base_snapshot
):
    """Test saving a nested value creates necessary tables."""
    # Arrange
    user_toml_path = mock_home_dir
    setting_path = 'sandbox.timeout'
    new_value = 120
    expected_toml_content = f'[sandbox]\ntimeout = {new_value}\n'

    # Ensure runtime and snapshot allow saving (assume default is different)
    base_app_config.sandbox.timeout = 60  # Simulate current runtime from TOML
    base_snapshot.sandbox.timeout = 60  # Simulate snapshot from TOML
    base_app_config.set_toml_snapshot(base_snapshot)

    # Act
    saved = save_setting_to_user_toml(base_app_config, setting_path, new_value)

    # Assert
    assert saved is True
    assert user_toml_path.exists()
    content = user_toml_path.read_text()
    assert content == expected_toml_content


def test_save_preserves_comments_and_other_values(
    mock_home_dir, base_app_config, base_snapshot
):
    """Test that saving preserves existing comments and unrelated values."""
    # Arrange
    user_toml_path = mock_home_dir
    setting_path = 'llm.model'
    new_value = 'new-model-for-test'

    initial_toml_content = """
# This is a comment
[core]
max_iterations = 100 # Another comment

[llm]
model = "old-model" # Will be changed
api_key = "keep-this-key"
"""
    expected_toml_content = f"""
# This is a comment
[core]
max_iterations = 100 # Another comment

[llm]
model = "{new_value}" # Will be changed
api_key = "keep-this-key"
"""
    user_toml_path.parent.mkdir(parents=True, exist_ok=True)
    user_toml_path.write_text(initial_toml_content)

    # Set runtime and snapshot to allow saving
    base_app_config.llm.model = 'old-model'
    base_snapshot.llm.model = 'old-model'
    # Set other values to match initial TOML for simplicity in this test
    base_app_config.max_iterations = 100
    base_snapshot.max_iterations = 100
    base_app_config.llm.api_key = 'keep-this-key'
    base_snapshot.llm.api_key = 'keep-this-key'
    base_app_config.set_toml_snapshot(base_snapshot)

    # Act
    saved = save_setting_to_user_toml(base_app_config, setting_path, new_value)

    # Assert
    assert saved is True
    content_after_save = user_toml_path.read_text()

    # Parse both to ignore minor whitespace differences from tomlkit
    doc_expected = tomlkit.parse(expected_toml_content)
    doc_actual = tomlkit.parse(content_after_save)
    assert doc_actual.as_string() == doc_expected.as_string()


# =============================================
# Tests for load_app_config snapshot creation
# =============================================


# Mock load_from_toml and load_from_env to isolate snapshot creation
@mock.patch('openhands.core.config.utils.load_from_env')
@mock.patch('openhands.core.config.utils.load_from_toml')
def test_load_app_config_creates_snapshot(mock_load_toml, mock_load_env, mock_home_dir):
    """Verify snapshot is taken after TOML loads and before ENV load."""
    # Arrange
    project_config_path = 'config.toml'  # Default path used by load_app_config
    user_config_path_str = str(mock_home_dir)  # Mocked user path

    # Define side effects for mocked load_from_toml
    # First call (project): sets model='project-model'
    # Second call (user): sets model='user-model', timeout=100
    # Snapshot should capture model='user-model', timeout=100
    # Env call: sets model='env-model'
    def load_toml_side_effect(config, path):
        if path == project_config_path:
            config.llm.model = 'project-model'
            print(f'Mock load_from_toml({path}): set model=project-model')
        elif path == user_config_path_str:
            config.llm.model = 'user-model'  # Overrides project
            config.sandbox.timeout = 100
            print(f'Mock load_from_toml({path}): set model=user-model, timeout=100')
        else:
            print(f'Mock load_from_toml({path}): unexpected path')

    def load_env_side_effect(config, env):
        config.llm.model = 'env-model'  # Overrides user
        config.max_iterations = 50  # New value from env
        print('Mock load_from_env: set model=env-model, max_iterations=50')

    mock_load_toml.side_effect = load_toml_side_effect
    mock_load_env.side_effect = load_env_side_effect

    # Act
    final_config = load_app_config(config_file=project_config_path)
    snapshot = final_config.get_toml_snapshot()

    # Assert
    assert snapshot is not None
    # Snapshot should reflect state after user TOML load
    assert snapshot.llm.model == 'user-model'
    assert snapshot.sandbox.timeout == 100
    # max_iterations wasn't set by TOML, should have default in snapshot
    assert snapshot.max_iterations == AppConfig().max_iterations

    # Final config should reflect state after ENV load
    assert final_config.llm.model == 'env-model'
    assert final_config.sandbox.timeout == 100  # Unchanged by env
    assert final_config.max_iterations == 50  # Changed by env

    # Check mock calls order (optional but good)
    assert mock_load_toml.call_count == 2
    mock_load_env.assert_called_once()


# TODO: Add more tests:
# - Test save_setting_to_user_toml with invalid setting_path
# - Test save_setting_to_user_toml error handling for file I/O
# - Test _get_value_from_path and _get_default_from_path helpers directly? (Maybe less critical if covered by save tests)
# - Test setup_config_from_args correctly passes snapshot through (if needed later)
