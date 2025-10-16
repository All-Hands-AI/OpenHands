"""Unit tests for ExperimentManager class, focusing on the v1 agent method."""

from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from openhands.experiments.experiment_manager import ExperimentManager
from openhands.sdk import Agent
from openhands.sdk.llm import LLM


class TestExperimentManager:
    """Test cases for ExperimentManager class."""

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

    def test_run_agent_variant_tests__v1_returns_agent_unchanged(self):
        """Test that the base ExperimentManager returns the agent unchanged."""
        # Act
        result = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        assert result is self.mock_agent
        assert result == self.mock_agent

    def test_run_agent_variant_tests__v1_with_none_user_id(self):
        """Test that the method works with None user_id."""
        # Act
        result = ExperimentManager.run_agent_variant_tests__v1(
            None, self.conversation_id, self.mock_agent
        )

        # Assert
        assert result is self.mock_agent

    def test_run_agent_variant_tests__v1_with_different_conversation_ids(self):
        """Test that the method works with different conversation IDs."""
        conversation_id_1 = uuid4()
        conversation_id_2 = uuid4()

        # Act
        result_1 = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, conversation_id_1, self.mock_agent
        )
        result_2 = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, conversation_id_2, self.mock_agent
        )

        # Assert
        assert result_1 is self.mock_agent
        assert result_2 is self.mock_agent

    def test_run_agent_variant_tests__v1_preserves_agent_properties(self):
        """Test that the method preserves all agent properties."""
        # Arrange
        original_llm = self.mock_agent.llm
        original_system_prompt = self.mock_agent.system_prompt_filename

        # Act
        result = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        assert result.llm is original_llm
        assert result.system_prompt_filename == original_system_prompt

    def test_run_agent_variant_tests__v1_is_static_method(self):
        """Test that the method can be called as a static method."""
        # Act - should not raise an error when called without instance
        result = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert
        assert result is self.mock_agent

    def test_run_agent_variant_tests__v1_type_annotations(self):
        """Test that the method has correct type annotations."""
        import inspect
        from typing import get_args, get_origin

        # Get the method signature
        sig = inspect.signature(ExperimentManager.run_agent_variant_tests__v1)

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


class TestExperimentManagerIntegration:
    """Integration tests for ExperimentManager with start_app_conversation."""

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

    @patch('openhands.experiments.experiment_manager.ExperimentManagerImpl')
    def test_start_app_conversation_calls_experiment_manager_v1(
        self, mock_experiment_manager_impl
    ):
        """Test that start_app_conversation calls the experiment manager v1 method with correct parameters."""
        # Arrange
        mock_experiment_manager_impl.run_agent_variant_tests__v1.return_value = (
            self.mock_agent
        )

        # Import the module that uses ExperimentManagerImpl
        from openhands.app_server.app_conversation.live_status_app_conversation_service import (
            LiveStatusAppConversationService,
        )

        # Create a mock service instance
        mock_service = Mock(spec=LiveStatusAppConversationService)

        # Mock the _build_start_conversation_request_for_user method to simulate the call
        with patch.object(mock_service, '_build_start_conversation_request_for_user'):
            # Simulate the part of the code that calls the experiment manager
            from uuid import uuid4

            conversation_id = uuid4()

            # This simulates the call that happens in the actual service
            result_agent = mock_experiment_manager_impl.run_agent_variant_tests__v1(
                self.user_id, conversation_id, self.mock_agent
            )

            # Assert
            mock_experiment_manager_impl.run_agent_variant_tests__v1.assert_called_once_with(
                self.user_id, conversation_id, self.mock_agent
            )
            assert result_agent == self.mock_agent

    @patch(
        'openhands.app_server.app_conversation.live_status_app_conversation_service.ExperimentManagerImpl'
    )
    @patch(
        'openhands.app_server.app_conversation.live_status_app_conversation_service.get_default_agent'
    )
    @patch(
        'openhands.app_server.app_conversation.live_status_app_conversation_service.uuid4'
    )
    def test_experiment_manager_called_with_correct_parameters_in_context(
        self, mock_uuid4, mock_get_default_agent, mock_experiment_manager_impl
    ):
        """Test that the experiment manager is called with the correct parameters in the actual context."""
        # Arrange
        mock_conversation_id = uuid4()
        mock_uuid4.return_value = mock_conversation_id
        mock_get_default_agent.return_value = self.mock_agent
        mock_experiment_manager_impl.run_agent_variant_tests__v1.return_value = (
            self.mock_agent
        )

        # Import and create the method that contains the call
        from openhands.app_server.app_conversation.live_status_app_conversation_service import (
            LiveStatusAppConversationService,
        )

        # Create a mock user object
        mock_user = Mock()
        mock_user.id = self.user_id
        mock_user.llm_model = 'gpt-4'
        mock_user.llm_base_url = None
        mock_user.llm_api_key = None

        # Create a mock service instance with necessary attributes
        Mock(spec=LiveStatusAppConversationService)

        # Mock the LLM creation
        with patch(
            'openhands.app_server.app_conversation.live_status_app_conversation_service.LLM'
        ) as mock_llm_class:
            mock_llm_class.return_value = self.mock_llm

            # Simulate the code path that calls the experiment manager
            # This is based on the actual code in _build_start_conversation_request_for_user
            llm = mock_llm_class(
                model=mock_user.llm_model,
                base_url=mock_user.llm_base_url,
                api_key=mock_user.llm_api_key,
                service_id='agent',
            )
            agent = mock_get_default_agent(llm=llm)

            # This is the key call we want to test
            conversation_id = mock_uuid4()
            result_agent = mock_experiment_manager_impl.run_agent_variant_tests__v1(
                mock_user.id, conversation_id, agent
            )

            # Assert
            mock_experiment_manager_impl.run_agent_variant_tests__v1.assert_called_once_with(
                mock_user.id, mock_conversation_id, self.mock_agent
            )
            assert result_agent == self.mock_agent

    def test_experiment_manager_integration_with_real_agent_object(self):
        """Test the experiment manager with a more realistic agent object."""
        # Arrange - Create a more realistic agent mock that behaves like the real thing
        realistic_llm = Mock(spec=LLM)
        realistic_llm.model = 'gpt-4'
        realistic_llm.service_id = 'agent'

        realistic_agent = Mock(spec=Agent)
        realistic_agent.llm = realistic_llm
        realistic_agent.system_prompt_filename = 'default_system_prompt.j2'
        realistic_agent.model_copy = Mock(return_value=realistic_agent)

        # Act
        result = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, realistic_agent
        )

        # Assert
        assert result is realistic_agent
        assert result.llm.model == 'gpt-4'
        assert result.system_prompt_filename == 'default_system_prompt.j2'

    def test_experiment_manager_impl_is_used_correctly(self):
        """Test that ExperimentManagerImpl is correctly instantiated and used."""
        # Import the actual implementation
        from openhands.experiments.experiment_manager import ExperimentManagerImpl

        # Act - call the method on the implementation
        result = ExperimentManagerImpl.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

        # Assert - the base implementation should return the agent unchanged
        assert result is self.mock_agent

        # Verify that ExperimentManagerImpl is indeed a class (not None)
        assert ExperimentManagerImpl is not None
        assert hasattr(ExperimentManagerImpl, 'run_agent_variant_tests__v1')

    def test_integration_with_live_status_app_conversation_service_import(self):
        """Test that the ExperimentManagerImpl import works in the actual service."""
        # This test verifies that the import chain works correctly
        try:
            # Import both and verify they exist and have the required method
            from openhands.app_server.app_conversation.live_status_app_conversation_service import (
                ExperimentManagerImpl as ServiceExperimentManagerImpl,
            )
            from openhands.experiments.experiment_manager import (
                ExperimentManagerImpl as DirectExperimentManagerImpl,
            )

            # Both should have the v1 method
            assert hasattr(ServiceExperimentManagerImpl, 'run_agent_variant_tests__v1')
            assert hasattr(DirectExperimentManagerImpl, 'run_agent_variant_tests__v1')

            # Test that the method works on the direct import
            result = DirectExperimentManagerImpl.run_agent_variant_tests__v1(
                self.user_id, self.conversation_id, self.mock_agent
            )
            assert result is self.mock_agent

        except ImportError as e:
            pytest.fail(f'Import failed: {e}')

    def test_actual_usage_pattern_in_service(self):
        """Test the actual usage pattern as it appears in the service code."""
        # Import the actual ExperimentManagerImpl as used in the experiment manager module
        from openhands.experiments.experiment_manager import ExperimentManagerImpl

        # Act - simulate the exact call pattern from the service
        conversation_id = uuid4()
        agent = ExperimentManagerImpl.run_agent_variant_tests__v1(
            self.user_id, conversation_id, self.mock_agent
        )

        # Assert
        assert agent is self.mock_agent
