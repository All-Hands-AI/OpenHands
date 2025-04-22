from unittest.mock import MagicMock, PropertyMock, mock_open, patch

import toml

from openhands.core.cli_tui import UsageMetrics
from openhands.core.cli_utils import (
    extract_model_and_provider,
    is_number,
    manage_openhands_file,
    organize_models_and_providers,
    read_file,
    split_is_actually_version,
    update_usage_metrics,
    write_to_file,
)
from openhands.events.event import Event
from openhands.llm.metrics import Metrics, TokenUsage


class TestManageOpenhandsFile:
    @patch('openhands.core.cli_utils.Path')
    @patch('openhands.core.cli_utils.toml.dump')
    def test_manage_openhands_file_create_new(self, mock_toml_dump, mock_path):
        # Setup mock path
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_file = MagicMock()
        mock_home.__truediv__.return_value = mock_file
        mock_file.exists.return_value = False

        # Setup mock file open
        mock_open_file = mock_open()
        with patch('builtins.open', mock_open_file):
            result = manage_openhands_file()

        # Assertions
        assert result is False
        mock_path.home.assert_called_once()
        mock_home.__truediv__.assert_called_once_with('.openhands.toml')
        mock_file.exists.assert_called_once()
        mock_open_file.assert_called_once_with(mock_file, 'w')

        # Check toml dump was called with expected data
        expected_data = {'trusted_dirs': []}
        mock_toml_dump.assert_called_once_with(expected_data, mock_open_file())

    @patch('openhands.core.cli_utils.Path')
    def test_manage_openhands_file_folder_not_trusted(self, mock_path):
        # Setup mock path
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_file = MagicMock()
        mock_home.__truediv__.return_value = mock_file
        mock_file.exists.return_value = True

        config_data = {'trusted_dirs': ['/other/path']}

        # Setup mock file open
        mock_open_file = mock_open(read_data=toml.dumps(config_data))
        with patch('builtins.open', mock_open_file):
            with patch('openhands.core.cli_utils.toml.load') as mock_toml_load:
                mock_toml_load.return_value = config_data
                result = manage_openhands_file('/test/path')

        # Assertions
        assert result is False
        mock_open_file.assert_called_with(mock_file, 'r')

    @patch('openhands.core.cli_utils.Path')
    def test_manage_openhands_file_folder_already_trusted(self, mock_path):
        # Setup mock path
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_file = MagicMock()
        mock_home.__truediv__.return_value = mock_file
        mock_file.exists.return_value = True

        test_path = '/test/path'
        config_data = {'trusted_dirs': [test_path]}

        # Setup mock file open
        mock_open_file = mock_open(read_data=toml.dumps(config_data))
        with patch('builtins.open', mock_open_file):
            with patch('openhands.core.cli_utils.toml.load') as mock_toml_load:
                mock_toml_load.return_value = config_data
                result = manage_openhands_file(test_path)

        # Assertions
        assert result is True

    @patch('openhands.core.cli_utils.Path')
    @patch('openhands.core.cli_utils.toml.dump')
    def test_manage_openhands_file_add_trusted(self, mock_toml_dump, mock_path):
        # Setup mock path
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_file = MagicMock()
        mock_home.__truediv__.return_value = mock_file
        mock_file.exists.return_value = True

        test_path = '/test/path'
        config_data = {'trusted_dirs': ['/other/path']}

        # Setup mock file open
        mock_open_file = mock_open(read_data=toml.dumps(config_data))
        with patch('builtins.open', mock_open_file):
            with patch('openhands.core.cli_utils.toml.load') as mock_toml_load:
                mock_toml_load.return_value = config_data
                result = manage_openhands_file(test_path, add_to_trusted=True)

        # Assertions
        assert result is False
        expected_config = {'trusted_dirs': ['/other/path', test_path]}
        mock_toml_dump.assert_called_once_with(expected_config, mock_open_file())


class TestUpdateUsageMetrics:
    def test_update_usage_metrics_no_llm_metrics(self):
        event = Event()
        usage_metrics = UsageMetrics()

        original_cost = usage_metrics.total_cost
        original_input = usage_metrics.total_input_tokens
        original_output = usage_metrics.total_output_tokens

        update_usage_metrics(event, usage_metrics)

        # Metrics should remain unchanged
        assert usage_metrics.total_cost == original_cost
        assert usage_metrics.total_input_tokens == original_input
        assert usage_metrics.total_output_tokens == original_output

    def test_update_usage_metrics_with_cost(self):
        event = Event()
        # Create a mock Metrics object
        metrics = MagicMock(spec=Metrics)
        # Mock the accumulated_cost property
        type(metrics).accumulated_cost = PropertyMock(return_value=1.25)
        event.llm_metrics = metrics

        usage_metrics = UsageMetrics()

        update_usage_metrics(event, usage_metrics)

        assert usage_metrics.total_cost == 1.25
        assert usage_metrics.total_input_tokens == 0
        assert usage_metrics.total_output_tokens == 0

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

        assert usage_metrics.total_cost == 1.5
        assert usage_metrics.total_input_tokens == 100
        assert usage_metrics.total_output_tokens == 50
        assert usage_metrics.total_cache_read == 20
        assert usage_metrics.total_cache_write == 30

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

        # Metrics should remain at zero since invalid types were provided
        assert usage_metrics.total_cost == 0
        assert usage_metrics.total_input_tokens == 0
        assert usage_metrics.total_output_tokens == 0
        assert usage_metrics.total_cache_read == 0
        assert usage_metrics.total_cache_write == 0


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
        model = 'claude-3-7-sonnet-20250219'
        result = extract_model_and_provider(model)

        assert result['provider'] == 'anthropic'
        assert result['model'] == 'claude-3-7-sonnet-20250219'
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
            'anthropic/claude-3-7-sonnet-20250219',
            'o3-mini',
            'anthropic.claude-3-5',  # Should be ignored as it uses dot separator for anthropic
            'unknown-model',
        ]

        result = organize_models_and_providers(models)

        assert 'openai' in result
        assert 'anthropic' in result
        assert 'other' in result

        assert len(result['openai']['models']) == 2
        assert 'gpt-4o' in result['openai']['models']
        assert 'o3-mini' in result['openai']['models']

        assert len(result['anthropic']['models']) == 1
        assert 'claude-3-7-sonnet-20250219' in result['anthropic']['models']

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
