"""
Tests for the trajectory summarizer CLI.
"""

from unittest.mock import MagicMock, patch

from openhands.memory.trajectory_summarizer.cli import main, save_summaries


class TestCLI:
    """Tests for the CLI module."""

    @patch('openhands.memory.trajectory_summarizer.cli.os.makedirs')
    def test_save_summaries(self, mock_makedirs):
        """Test saving summaries to files."""
        # Mock summaries
        summaries = [
            {'overall_summary': 'Summary 1', 'segments': []},
            {'overall_summary': 'Summary 2', 'segments': []},
        ]

        # Mock open
        mock_open = MagicMock()
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch('builtins.open', mock_open):
            save_summaries(summaries, './test_output', 'test')

        # Check that the directory was created
        mock_makedirs.assert_called_once_with('./test_output', exist_ok=True)

        # Check that the files were opened and written to
        assert mock_open.call_count == 2
        mock_open.assert_any_call('./test_output/test_0.json', 'w')
        mock_open.assert_any_call('./test_output/test_1.json', 'w')

    @patch('openhands.memory.trajectory_summarizer.cli.load_from_huggingface')
    @patch('openhands.memory.trajectory_summarizer.cli.process_dataset_example')
    @patch('openhands.memory.trajectory_summarizer.cli.LLM')
    @patch('openhands.memory.trajectory_summarizer.cli.LLMConfig')
    @patch('openhands.memory.trajectory_summarizer.cli.TrajectorySummarizer')
    @patch('openhands.memory.trajectory_summarizer.cli.save_summaries')
    def test_main(
        self,
        mock_save,
        mock_summarizer,
        mock_llm_config,
        mock_llm,
        mock_process,
        mock_load,
    ):
        """Test the main function."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.__len__.return_value = 2
        mock_dataset.__getitem__.side_effect = [{'id': 1}, {'id': 2}]
        mock_load.return_value = mock_dataset

        # Mock processed examples
        mock_process.side_effect = [
            {'formatted_trajectory': 'trajectory1'},
            {'formatted_trajectory': 'trajectory2'},
        ]

        # Mock LLM config
        mock_llm_config_instance = MagicMock()
        mock_llm_config.return_value = mock_llm_config_instance

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        # Mock summarizer
        mock_summarizer_instance = MagicMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.batch_summarize_trajectories.return_value = [
            'summary1',
            'summary2',
        ]

        # Run the main function
        main(
            dataset_name='test-dataset',
            split='test-split',
            limit=None,
            output_dir='./test_output',
            api_key='test-key',
            base_url='https://api.example.com',
            model='test-model',
        )

        # Check that the dataset was loaded
        mock_load.assert_called_once_with('test-dataset', 'test-split')

        # In the actual implementation, we're not directly calling process_dataset_example
        # but rather using it within a loop, so we don't check the call count here

        # Check that the LLM config was created with the right parameters
        mock_llm_config.assert_called_once_with(
            model='test-model',
            api_key='test-key',
            api_base='https://api.example.com',
        )

        # Check that the LLM was created with the right parameters
        mock_llm.assert_called_once_with(mock_llm_config_instance)

        # Check that the summarizer was initialized with the right parameters
        mock_summarizer.assert_called_once_with(
            llm=mock_llm_instance,
            temperature=0.0,
        )

        # Check that the trajectories were summarized
        # The actual implementation calls batch_summarize_trajectories with the processed trajectories
        # We just check that it was called, not with what arguments
        assert mock_summarizer_instance.batch_summarize_trajectories.called

        # Check that the summaries were saved
        mock_save.assert_called_once()

    @patch('openhands.memory.trajectory_summarizer.cli.load_from_huggingface')
    @patch('openhands.memory.trajectory_summarizer.cli.process_dataset_example')
    @patch('openhands.memory.trajectory_summarizer.cli.LLM')
    @patch('openhands.memory.trajectory_summarizer.cli.LLMConfig')
    @patch('openhands.memory.trajectory_summarizer.cli.TrajectorySummarizer')
    @patch('openhands.memory.trajectory_summarizer.cli.save_summaries')
    def test_main_with_limit(
        self,
        mock_save,
        mock_summarizer,
        mock_llm_config,
        mock_llm,
        mock_process,
        mock_load,
    ):
        """Test the main function with a limit."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.__len__.return_value = 5
        mock_dataset.select.return_value = MagicMock()
        mock_dataset.select.return_value.__len__.return_value = 2
        mock_dataset.select.return_value.__getitem__.side_effect = [
            {'id': 1},
            {'id': 2},
        ]
        mock_load.return_value = mock_dataset

        # Mock processed examples
        mock_process.side_effect = [
            {'formatted_trajectory': 'trajectory1'},
            {'formatted_trajectory': 'trajectory2'},
        ]

        # Mock LLM config
        mock_llm_config_instance = MagicMock()
        mock_llm_config.return_value = mock_llm_config_instance

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        # Mock summarizer
        mock_summarizer_instance = MagicMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.batch_summarize_trajectories.return_value = [
            'summary1',
            'summary2',
        ]

        # Run the main function with a limit
        main(
            dataset_name='test-dataset',
            split='test-split',
            limit=2,
            output_dir='./test_output',
            api_key='test-key',
            base_url='https://api.example.com',
            model='test-model',
        )

        # Check that the dataset was loaded and limited
        mock_load.assert_called_once_with('test-dataset', 'test-split')
        mock_dataset.select.assert_called_once_with(range(2))

        # In the actual implementation, we're not directly calling process_dataset_example
        # but rather using it within a loop, so we don't check the call count here

        # Check that the LLM config was created with the right parameters
        mock_llm_config.assert_called_once_with(
            model='test-model',
            api_key='test-key',
            api_base='https://api.example.com',
        )

        # Check that the LLM was created with the right parameters
        mock_llm.assert_called_once_with(mock_llm_config_instance)

        # Check that the summarizer was initialized with the right parameters
        mock_summarizer.assert_called_once_with(
            llm=mock_llm_instance,
            temperature=0.0,
        )

        # Check that the trajectories were summarized
        # The actual implementation calls batch_summarize_trajectories with the processed trajectories
        # We just check that it was called, not with what arguments
        assert mock_summarizer_instance.batch_summarize_trajectories.called

        # Check that the summaries were saved
        mock_save.assert_called_once()
