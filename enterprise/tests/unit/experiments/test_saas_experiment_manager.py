"""Unit tests for SaaSExperimentManager class, focusing on the v1 agent method."""

from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from experiments.experiment_manager import SaaSExperimentManager
from openhands.sdk import Agent
from openhands.sdk.llm import LLM


class TestSaaSExperimentManager:
    """Test cases for SaaSExperimentManager core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.user_id = 'test_user_123'
        self.conversation_id = uuid4()

        # Create a mock LLM
        self.mock_llm = Mock(spec=LLM)
        self.mock_llm.model = 'gpt-4'
        self.mock_llm.service_id = 'agent'

        # Create a mock Agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.llm = self.mock_llm
        self.mock_agent.system_prompt_filename = 'default_system_prompt.j2'
        self.mock_agent.model_copy = Mock(return_value=self.mock_agent)

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_run_agent_variant_tests__v1_with_experiment_enabled(
        self, mock_condenser_experiment
    ):
        """Test that the method processes experiments when enabled."""
        # Arrange
        mock_condenser_experiment.return_value = self.mock_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        mock_condenser_experiment.assert_called_once_with(
            self.user_id, self.conversation_id, self.mock_agent
        )
        # Verify system prompt is updated
        self.mock_agent.model_copy.assert_called_once_with(
            update={'system_prompt_filename': 'system_prompt_long_horizon.j2'}
        )
        assert result is self.mock_agent

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', False)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_run_agent_variant_tests__v1_with_experiment_disabled(
        self, mock_condenser_experiment
    ):
        """Test that the method returns agent unchanged when experiments are disabled."""
        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        mock_condenser_experiment.assert_not_called()
        self.mock_agent.model_copy.assert_not_called()
        assert result is self.mock_agent

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_run_agent_variant_tests__v1_with_none_user_id(
        self, mock_condenser_experiment
    ):
        """Test that the method works with None user_id."""
        # Arrange
        mock_condenser_experiment.return_value = self.mock_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            None, self.conversation_id, self.mock_agent
        )

        # Assert
        mock_condenser_experiment.assert_called_once_with(
            None, self.conversation_id, self.mock_agent
        )
        assert result is self.mock_agent

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_run_agent_variant_tests__v1_with_different_conversation_ids(
        self, mock_condenser_experiment
    ):
        """Test that the method works with different conversation IDs."""
        # Arrange
        conversation_id_1 = uuid4()
        conversation_id_2 = uuid4()
        mock_condenser_experiment.return_value = self.mock_agent

        # Act
        result_1 = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, conversation_id_1, self.mock_agent
        )
        result_2 = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, conversation_id_2, self.mock_agent
        )

        # Assert
        assert mock_condenser_experiment.call_count == 2
        mock_condenser_experiment.assert_any_call(
            self.user_id, conversation_id_1, self.mock_agent
        )
        mock_condenser_experiment.assert_any_call(
            self.user_id, conversation_id_2, self.mock_agent
        )
        assert result_1 is self.mock_agent
        assert result_2 is self.mock_agent

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_run_agent_variant_tests__v1_preserves_agent_properties(
        self, mock_condenser_experiment
    ):
        """Test that the method preserves agent properties through the experiment chain."""
        # Arrange
        mock_condenser_experiment.return_value = self.mock_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        assert result.llm is self.mock_llm
        # Verify the system prompt is updated to the long horizon version
        self.mock_agent.model_copy.assert_called_once_with(
            update={'system_prompt_filename': 'system_prompt_long_horizon.j2'}
        )

    def test_run_agent_variant_tests__v1_is_static_method(self):
        """Test that the method is a static method."""
        # Act & Assert
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )
        assert result is self.mock_agent

    def test_run_agent_variant_tests__v1_type_annotations(self):
        """Test that the method has correct type annotations."""
        import inspect
        from typing import get_args, get_origin

        # Get the method signature
        sig = inspect.signature(SaaSExperimentManager.run_agent_variant_tests__v1)

        # Check parameter types - handle Union types properly
        user_id_annotation = sig.parameters['user_id'].annotation
        # Check if it's a Union type (str | None)
        if hasattr(user_id_annotation, '__origin__'):
            assert get_origin(user_id_annotation) is type(str | None).__origin__
            assert str in get_args(user_id_annotation)
            assert type(None) in get_args(user_id_annotation)
        else:
            # Fallback for different Python versions
            assert 'str' in str(user_id_annotation) and 'None' in str(
                user_id_annotation
            )

        assert sig.parameters['conversation_id'].annotation == UUID
        assert sig.parameters['agent'].annotation == Agent

        # Check return type
        assert sig.return_annotation == Agent


class TestSaaSExperimentManagerIntegration:
    """Integration tests for SaaSExperimentManager with other components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.user_id = 'test_user_123'
        self.conversation_id = uuid4()

        # Create a mock LLM
        self.mock_llm = Mock(spec=LLM)
        self.mock_llm.model = 'gpt-4'
        self.mock_llm.service_id = 'agent'

        # Create a mock Agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.llm = self.mock_llm
        self.mock_agent.system_prompt_filename = 'default_system_prompt.j2'
        self.mock_agent.model_copy = Mock(return_value=self.mock_agent)

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_condenser_experiment_integration(self, mock_condenser_experiment):
        """Test integration with condenser max step experiment."""
        # Arrange
        modified_agent = Mock(spec=Agent)
        modified_agent.llm = self.mock_llm
        modified_agent.system_prompt_filename = 'default_system_prompt.j2'
        modified_agent.model_copy = Mock(return_value=modified_agent)
        mock_condenser_experiment.return_value = modified_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        mock_condenser_experiment.assert_called_once_with(
            self.user_id, self.conversation_id, self.mock_agent
        )
        # Verify system prompt update is applied to the modified agent
        modified_agent.model_copy.assert_called_once_with(
            update={'system_prompt_filename': 'system_prompt_long_horizon.j2'}
        )
        assert result is modified_agent

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    @patch('experiments.experiment_manager.logger')
    def test_logging_when_experiment_disabled(
        self, mock_logger, mock_condenser_experiment
    ):
        """Test that appropriate logging occurs when experiments are disabled."""
        # Arrange
        with patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', False):
            # Act
            result = SaaSExperimentManager.run_agent_variant_tests__v1(
                self.user_id, self.conversation_id, self.mock_agent
            )

            # Assert
            mock_logger.info.assert_called_once_with(
                'experiment_manager:run_conversation_variant_test:skipped',
                extra={'reason': 'experiment_manager_disabled'},
            )
            mock_condenser_experiment.assert_not_called()
            assert result is self.mock_agent

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_system_prompt_update_behavior(self, mock_condenser_experiment):
        """Test that system prompt is always updated to long horizon version."""
        # Arrange
        mock_condenser_experiment.return_value = self.mock_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        self.mock_agent.model_copy.assert_called_once_with(
            update={'system_prompt_filename': 'system_prompt_long_horizon.j2'}
        )
        assert result is self.mock_agent

    def test_experiment_manager_inheritance(self):
        """Test that SaaSExperimentManager properly inherits from ExperimentManager."""
        from openhands.experiments.experiment_manager import ExperimentManager

        # Assert
        assert issubclass(SaaSExperimentManager, ExperimentManager)
        assert hasattr(SaaSExperimentManager, 'run_agent_variant_tests__v1')

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_experiment_chain_execution_order(self, mock_condenser_experiment):
        """Test that experiments are executed in the correct order."""
        # Arrange
        intermediate_agent = Mock(spec=Agent)
        intermediate_agent.llm = self.mock_llm
        intermediate_agent.system_prompt_filename = 'default_system_prompt.j2'
        final_agent = Mock(spec=Agent)
        final_agent.llm = self.mock_llm
        final_agent.system_prompt_filename = 'system_prompt_long_horizon.j2'

        mock_condenser_experiment.return_value = intermediate_agent
        intermediate_agent.model_copy.return_value = final_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert - verify execution order
        # 1. First, condenser experiment is called
        mock_condenser_experiment.assert_called_once_with(
            self.user_id, self.conversation_id, self.mock_agent
        )
        # 2. Then, system prompt is updated
        intermediate_agent.model_copy.assert_called_once_with(
            update={'system_prompt_filename': 'system_prompt_long_horizon.j2'}
        )
        # 3. Final result is the agent with updated system prompt
        assert result is final_agent

    def test_import_verification(self):
        """Test that all required imports are available and working."""
        # This test verifies that the import chain works correctly
        try:
            # Import and verify they exist and have the required method
            from experiments.experiment_manager import SaaSExperimentManager

            # Should have the v1 method
            assert hasattr(SaaSExperimentManager, 'run_agent_variant_tests__v1')

            # Test that the method works on the direct import
            mock_agent = Mock(spec=Agent)
            result = SaaSExperimentManager.run_agent_variant_tests__v1(
                self.user_id, self.conversation_id, mock_agent
            )
            assert result is mock_agent

        except ImportError as e:
            pytest.fail(f'Import failed: {e}')

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_realistic_agent_object_handling(self, mock_condenser_experiment):
        """Test the experiment manager with a more realistic agent object."""
        # Arrange - Create a more realistic agent mock that behaves like the real thing
        realistic_llm = Mock(spec=LLM)
        realistic_llm.model = 'gpt-4'
        realistic_llm.service_id = 'agent'
        realistic_llm.model_copy = Mock(return_value=realistic_llm)

        realistic_agent = Mock(spec=Agent)
        realistic_agent.llm = realistic_llm
        realistic_agent.system_prompt_filename = 'default_system_prompt.j2'

        # Create the final agent with updated system prompt
        final_agent = Mock(spec=Agent)
        final_agent.llm = realistic_llm
        final_agent.system_prompt_filename = 'system_prompt_long_horizon.j2'

        realistic_agent.model_copy = Mock(return_value=final_agent)
        mock_condenser_experiment.return_value = realistic_agent

        # Act
        result = SaaSExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, realistic_agent
        )

        # Assert
        mock_condenser_experiment.assert_called_once_with(
            self.user_id, self.conversation_id, realistic_agent
        )
        realistic_agent.model_copy.assert_called_once_with(
            update={'system_prompt_filename': 'system_prompt_long_horizon.j2'}
        )
        assert result is final_agent
        assert result.llm.model == 'gpt-4'
        assert result.system_prompt_filename == 'system_prompt_long_horizon.j2'

    @patch('experiments.experiment_manager.ENABLE_EXPERIMENT_MANAGER', True)
    @patch('experiments.experiment_manager.handle_condenser_max_step_experiment__v1')
    def test_experiment_with_edge_case_inputs(self, mock_condenser_experiment):
        """Test the experiment manager with edge case inputs."""
        # Arrange
        mock_condenser_experiment.return_value = self.mock_agent

        # Test with empty string user_id
        result1 = SaaSExperimentManager.run_agent_variant_tests__v1(
            '', self.conversation_id, self.mock_agent
        )

        # Test with very long user_id
        long_user_id = 'a' * 1000
        result2 = SaaSExperimentManager.run_agent_variant_tests__v1(
            long_user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        assert result1 is self.mock_agent
        assert result2 is self.mock_agent
        assert mock_condenser_experiment.call_count == 2
        mock_condenser_experiment.assert_any_call(
            '', self.conversation_id, self.mock_agent
        )
        mock_condenser_experiment.assert_any_call(
            long_user_id, self.conversation_id, self.mock_agent
        )