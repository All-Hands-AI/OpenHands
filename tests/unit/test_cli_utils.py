from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

import toml

from openhands.cli.tui import UsageMetrics
from openhands.cli.utils import (
    add_local_config_trusted_dir,
    extract_model_and_provider,
    get_local_config_trusted_dirs,
    is_number,
    organize_models_and_providers,
    read_file,
    split_is_actually_version,
    update_usage_metrics,
    write_to_file,
)
from openhands.events.event import Event
from openhands.llm.metrics import Metrics, TokenUsage


class TestGetLocalConfigTrustedDirs:
    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    def test_config_file_does_not_exist(self, mock_config_path):
        mock_config_path.exists.return_value = False
        result = get_local_config_trusted_dirs()
        assert result == []
        mock_config_path.exists.assert_called_once()

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid toml')
    @patch(
        'openhands.cli.utils.toml.load',
        side_effect=toml.TomlDecodeError('error', 'doc', 0),
    )
    def test_config_file_invalid_toml(
        self, mock_toml_load, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        result = get_local_config_trusted_dirs()
        assert result == []
        mock_config_path.exists.assert_called_once()
        mock_open_file.assert_called_once_with(mock_config_path, 'r')
        mock_toml_load.assert_called_once()

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'sandbox': {'trusted_dirs': ['/path/one']}}),
    )
    @patch('openhands.cli.utils.toml.load')
    def test_config_file_valid(self, mock_toml_load, mock_open_file, mock_config_path):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'sandbox': {'trusted_dirs': ['/path/one']}}
        result = get_local_config_trusted_dirs()
        assert result == ['/path/one']
        mock_config_path.exists.assert_called_once()
        mock_open_file.assert_called_once_with(mock_config_path, 'r')
        mock_toml_load.assert_called_once()

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'other_section': {}}),
    )
    @patch('openhands.cli.utils.toml.load')
    def test_config_file_missing_sandbox(
        self, mock_toml_load, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'other_section': {}}
        result = get_local_config_trusted_dirs()
        assert result == []
        mock_config_path.exists.assert_called_once()
        mock_open_file.assert_called_once_with(mock_config_path, 'r')
        mock_toml_load.assert_called_once()

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'sandbox': {'other_key': []}}),
    )
    @patch('openhands.cli.utils.toml.load')
    def test_config_file_missing_trusted_dirs(
        self, mock_toml_load, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'sandbox': {'other_key': []}}
        result = get_local_config_trusted_dirs()
        assert result == []
        mock_config_path.exists.assert_called_once()
        mock_open_file.assert_called_once_with(mock_config_path, 'r')
        mock_toml_load.assert_called_once()


class TestAddLocalConfigTrustedDir:
    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch('builtins.open', new_callable=mock_open)
    @patch('openhands.cli.utils.toml.dump')
    @patch('openhands.cli.utils.toml.load')
    def test_add_to_non_existent_file(
        self, mock_toml_load, mock_toml_dump, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = False
        mock_parent = MagicMock(spec=Path)
        mock_config_path.parent = mock_parent

        add_local_config_trusted_dir('/new/path')

        mock_config_path.exists.assert_called_once()
        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_open_file.assert_called_once_with(mock_config_path, 'w')
        expected_config = {'sandbox': {'trusted_dirs': ['/new/path']}}
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())
        mock_toml_load.assert_not_called()

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'sandbox': {'trusted_dirs': ['/old/path']}}),
    )
    @patch('openhands.cli.utils.toml.dump')
    @patch('openhands.cli.utils.toml.load')
    def test_add_to_existing_file(
        self, mock_toml_load, mock_toml_dump, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'sandbox': {'trusted_dirs': ['/old/path']}}

        add_local_config_trusted_dir('/new/path')

        mock_config_path.exists.assert_called_once()
        assert mock_open_file.call_count == 2  # Once for read, once for write
        mock_open_file.assert_any_call(mock_config_path, 'r')
        mock_open_file.assert_any_call(mock_config_path, 'w')
        mock_toml_load.assert_called_once()
        expected_config = {'sandbox': {'trusted_dirs': ['/old/path', '/new/path']}}
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'sandbox': {'trusted_dirs': ['/old/path']}}),
    )
    @patch('openhands.cli.utils.toml.dump')
    @patch('openhands.cli.utils.toml.load')
    def test_add_existing_dir(
        self, mock_toml_load, mock_toml_dump, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'sandbox': {'trusted_dirs': ['/old/path']}}

        add_local_config_trusted_dir('/old/path')

        mock_config_path.exists.assert_called_once()
        mock_toml_load.assert_called_once()
        expected_config = {
            'sandbox': {'trusted_dirs': ['/old/path']}
        }  # Should not change
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid toml')
    @patch('openhands.cli.utils.toml.dump')
    @patch(
        'openhands.cli.utils.toml.load',
        side_effect=toml.TomlDecodeError('error', 'doc', 0),
    )
    def test_add_to_invalid_toml(
        self, mock_toml_load, mock_toml_dump, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True

        add_local_config_trusted_dir('/new/path')

        mock_config_path.exists.assert_called_once()
        mock_toml_load.assert_called_once()
        expected_config = {
            'sandbox': {'trusted_dirs': ['/new/path']}
        }  # Should reset to default + new path
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'other_section': {}}),
    )
    @patch('openhands.cli.utils.toml.dump')
    @patch('openhands.cli.utils.toml.load')
    def test_add_to_missing_sandbox(
        self, mock_toml_load, mock_toml_dump, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'other_section': {}}

        add_local_config_trusted_dir('/new/path')

        mock_config_path.exists.assert_called_once()
        mock_toml_load.assert_called_once()
        expected_config = {
            'other_section': {},
            'sandbox': {'trusted_dirs': ['/new/path']},
        }
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())

    @patch('openhands.cli.utils._LOCAL_CONFIG_FILE_PATH')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data=toml.dumps({'sandbox': {'other_key': []}}),
    )
    @patch('openhands.cli.utils.toml.dump')
    @patch('openhands.cli.utils.toml.load')
    def test_add_to_missing_trusted_dirs(
        self, mock_toml_load, mock_toml_dump, mock_open_file, mock_config_path
    ):
        mock_config_path.exists.return_value = True
        mock_toml_load.return_value = {'sandbox': {'other_key': []}}

        add_local_config_trusted_dir('/new/path')

        mock_config_path.exists.assert_called_once()
        mock_toml_load.assert_called_once()
        expected_config = {'sandbox': {'other_key': [], 'trusted_dirs': ['/new/path']}}
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())


class TestUpdateUsageMetrics:
    def test_update_usage_metrics_no_llm_metrics(self):
        event = Event()
        usage_metrics = UsageMetrics()

        # Store original metrics object for comparison
        original_metrics = usage_metrics.metrics

        update_usage_metrics(event, usage_metrics)

        # Metrics should remain unchanged
        assert usage_metrics.metrics is original_metrics  # Same object reference
        assert usage_metrics.metrics.accumulated_cost == 0.0  # Default value

    def test_update_usage_metrics_with_cost(self):
        event = Event()
        # Create a mock Metrics object
        metrics = MagicMock(spec=Metrics)
        # Mock the accumulated_cost property
        type(metrics).accumulated_cost = PropertyMock(return_value=1.25)
        event.llm_metrics = metrics

        usage_metrics = UsageMetrics()

        update_usage_metrics(event, usage_metrics)

        # Test that the metrics object was updated to the one from the event
        assert usage_metrics.metrics is metrics  # Should be the same object reference
        # Test that we can access the accumulated_cost through the metrics property
        assert usage_metrics.metrics.accumulated_cost == 1.25

    def test_update_usage_metrics_with_tokens(self):
        event = Event()

        # Create mock token usage
        token_usage = MagicMock(spec=TokenUsage)
        token_usage.prompt_tokens = 100
        token_usage.completion_tokens = 50
        token_usage.cache_read_tokens = 20
        token_usage.cache_write_tokens = 30

        # Create mock metrics
        metrics = MagicMock(spec=Metrics)
        # Set the mock properties
        type(metrics).accumulated_cost = PropertyMock(return_value=1.5)
        type(metrics).accumulated_token_usage = PropertyMock(return_value=token_usage)

        event.llm_metrics = metrics

        usage_metrics = UsageMetrics()

        update_usage_metrics(event, usage_metrics)

        # Test that the metrics object was updated to the one from the event
        assert usage_metrics.metrics is metrics  # Should be the same object reference

        # Test we can access metrics values through the metrics property
        assert usage_metrics.metrics.accumulated_cost == 1.5
        assert usage_metrics.metrics.accumulated_token_usage is token_usage
        assert usage_metrics.metrics.accumulated_token_usage.prompt_tokens == 100
        assert usage_metrics.metrics.accumulated_token_usage.completion_tokens == 50
        assert usage_metrics.metrics.accumulated_token_usage.cache_read_tokens == 20
        assert usage_metrics.metrics.accumulated_token_usage.cache_write_tokens == 30

    def test_update_usage_metrics_with_invalid_types(self):
        event = Event()

        # Create mock token usage with invalid types
        token_usage = MagicMock(spec=TokenUsage)
        token_usage.prompt_tokens = 'not an int'
        token_usage.completion_tokens = 'not an int'
        token_usage.cache_read_tokens = 'not an int'
        token_usage.cache_write_tokens = 'not an int'

        # Create mock metrics
        metrics = MagicMock(spec=Metrics)
        # Set the mock properties
        type(metrics).accumulated_cost = PropertyMock(return_value='not a float')
        type(metrics).accumulated_token_usage = PropertyMock(return_value=token_usage)

        event.llm_metrics = metrics

        usage_metrics = UsageMetrics()

        update_usage_metrics(event, usage_metrics)

        # Test that the metrics object was still updated to the one from the event
        # Even though the values are invalid types, the metrics object reference should be updated
        assert usage_metrics.metrics is metrics  # Should be the same object reference

        # We can verify that we can access the properties through the metrics object
        # The invalid types are preserved since our update_usage_metrics function
        # simply assigns the metrics object without validation
        assert usage_metrics.metrics.accumulated_cost == 'not a float'
        assert usage_metrics.metrics.accumulated_token_usage is token_usage


class TestModelAndProviderFunctions:
    def test_extract_model_and_provider_slash_format(self):
        model = 'openai/gpt-4o'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'openai'
        assert result['model'] == 'gpt-4o'
        assert result['separator'] == '/'

    def test_extract_model_and_provider_dot_format(self):
        model = 'anthropic.claude-3-7'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'anthropic'
        assert result['model'] == 'claude-3-7'
        assert result['separator'] == '.'

    def test_extract_model_and_provider_openai_implicit(self):
        model = 'gpt-4o'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'openai'
        assert result['model'] == 'gpt-4o'
        assert result['separator'] == '/'

    def test_extract_model_and_provider_anthropic_implicit(self):
        model = 'claude-sonnet-4-20250514'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'anthropic'
        assert result['model'] == 'claude-sonnet-4-20250514'
        assert result['separator'] == '/'

    def test_extract_model_and_provider_mistral_implicit(self):
        model = 'devstral-small-2505'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'mistral'
        assert result['model'] == 'devstral-small-2505'
        assert result['separator'] == '/'

    def test_extract_model_and_provider_o4_mini(self):
        model = 'o4-mini'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'openai'
        assert result['model'] == 'o4-mini'
        assert result['separator'] == '/'

    def test_extract_model_and_provider_versioned(self):
        model = 'deepseek.deepseek-coder-1.3b'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'deepseek'
        assert result['model'] == 'deepseek-coder-1.3b'
        assert result['separator'] == '.'

    def test_extract_model_and_provider_unknown(self):
        model = 'unknown-model'
        result = extract_model_and_provider(model)

        assert result['provider'] == ''
        assert result['model'] == 'unknown-model'
        assert result['separator'] == ''

    def test_organize_models_and_providers(self):
        models = [
            'openai/gpt-4o',
            'anthropic/claude-sonnet-4-20250514',
            'o3-mini',
            'o4-mini',
            'devstral-small-2505',
            'mistral/devstral-small-2505',
            'anthropic.claude-3-5',  # Should be ignored as it uses dot separator for anthropic
            'unknown-model',
        ]

        result = organize_models_and_providers(models)

        assert 'openai' in result
        assert 'anthropic' in result
        assert 'mistral' in result
        assert 'other' in result

        assert len(result['openai']['models']) == 3
        assert 'gpt-4o' in result['openai']['models']
        assert 'o3-mini' in result['openai']['models']
        assert 'o4-mini' in result['openai']['models']

        assert len(result['anthropic']['models']) == 1
        assert 'claude-sonnet-4-20250514' in result['anthropic']['models']

        assert len(result['mistral']['models']) == 2
        assert 'devstral-small-2505' in result['mistral']['models']

        assert len(result['other']['models']) == 1
        assert 'unknown-model' in result['other']['models']


class TestUtilityFunctions:
    def test_is_number_with_digit(self):
        assert is_number('1') is True
        assert is_number('9') is True

    def test_is_number_with_letter(self):
        assert is_number('a') is False
        assert is_number('Z') is False

    def test_is_number_with_special_char(self):
        assert is_number('.') is False
        assert is_number('-') is False

    def test_split_is_actually_version_true(self):
        split = ['model', '1.0']
        assert split_is_actually_version(split) is True

    def test_split_is_actually_version_false(self):
        split = ['model', 'version']
        assert split_is_actually_version(split) is False

    def test_split_is_actually_version_single_item(self):
        split = ['model']
        assert split_is_actually_version(split) is False


class TestFileOperations:
    def test_read_file(self):
        mock_content = 'test file content'
        with patch('builtins.open', mock_open(read_data=mock_content)):
            result = read_file('test.txt')

        assert result == mock_content

    def test_write_to_file(self):
        mock_content = 'test file content'
        mock_file = mock_open()

        with patch('builtins.open', mock_file):
            write_to_file('test.txt', mock_content)

        mock_file.assert_called_once_with('test.txt', 'w')
        handle = mock_file()
        handle.write.assert_called_once_with(mock_content)
