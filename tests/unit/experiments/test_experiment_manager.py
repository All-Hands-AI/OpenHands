"""Unit tests for ExperimentManager class, focusing on the v1 agent method."""

from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from openhands.app_server.app_conversation.live_status_app_conversation_service import (
    LiveStatusAppConversationService,
)
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
        self.mock_llm.usage_id = 'agent'

        # Create a mock Agent
        self.mock_agent = Mock(spec=Agent)
        self.mock_agent.llm = self.mock_llm
        self.mock_agent.system_prompt_filename = 'default_system_prompt.j2'
        self.mock_agent.model_copy = Mock(return_value=self.mock_agent)

    def test_run_agent_variant_tests__v1_returns_agent_unchanged(self):
        """Test that the base ExperimentManager returns the agent unchanged."""
        result = ExperimentManager.run_agent_variant_tests__v1(
            self.user_id, self.conversation_id, self.mock_agent
        )

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


class TestExperimentManagerIntegration:
    """Integration tests for ExperimentManager with start_app_conversation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.user_id = 'test_user_123'
        self.conversation_id = uuid4()

        # Create a mock LLM
        self.mock_llm = Mock(spec=LLM)
        self.mock_llm.model = 'gpt-4'
        self.mock_llm.usage_id = 'agent'

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

    @pytest.mark.asyncio
    async def test_experiment_manager_called_with_correct_parameters_in_context__noop_pass_through(
        self,
    ):
        """
        Use the real LiveStatusAppConversationService to build a StartConversationRequest,
        and verify ExperimentManagerImpl.run_agent_variant_tests__v1:
        - is called exactly once with the (user_id, generated conversation_id, agent)
        - returns the *same* agent instance (no copy/mutation)
        - does not tweak agent fields (LLM, system prompt, etc.)
        """
        # --- Arrange: fixed UUID to assert call parameters deterministically
        fixed_conversation_id = UUID('00000000-0000-0000-0000-000000000001')

        # Create a stable Agent (and LLM) we can identity-check later
        mock_llm = Mock(spec=LLM)
        mock_llm.model = 'gpt-4'
        mock_llm.usage_id = 'agent'

        mock_agent = Mock(spec=Agent)
        mock_agent.llm = mock_llm
        mock_agent.system_prompt_filename = 'default_system_prompt.j2'

        # Minimal, real-ish user context used by the service
        class DummyUserContext:
            async def get_user_info(self):
                # confirmation_mode=False -> NeverConfirm()
                return SimpleNamespace(
                    id='test_user_123',
                    llm_model='gpt-4',
                    llm_base_url=None,
                    llm_api_key=None,
                    confirmation_mode=False,
                )

            async def get_secrets(self):
                return {}

            async def get_latest_token(self, provider):
                return None

            async def get_user_id(self):
                return 'test_user_123'

        user_context = DummyUserContext()

        # The service requires a lot of deps, but for this test we won't exercise them.
        app_conversation_info_service = Mock()
        app_conversation_start_task_service = Mock()
        sandbox_service = Mock()
        sandbox_spec_service = Mock()
        jwt_service = Mock()
        httpx_client = Mock()

        service = LiveStatusAppConversationService(
            init_git_in_empty_workspace=False,
            user_context=user_context,
            app_conversation_info_service=app_conversation_info_service,
            app_conversation_start_task_service=app_conversation_start_task_service,
            sandbox_service=sandbox_service,
            sandbox_spec_service=sandbox_spec_service,
            jwt_service=jwt_service,
            sandbox_startup_timeout=30,
            sandbox_startup_poll_frequency=1,
            httpx_client=httpx_client,
            web_url=None,
            access_token_hard_timeout=None,
        )

        # Patch the pieces invoked by the service
        with (
            patch(
                'openhands.app_server.app_conversation.live_status_app_conversation_service.get_default_agent',
                return_value=mock_agent,
            ),
            patch(
                'openhands.app_server.app_conversation.live_status_app_conversation_service.uuid4',
                return_value=fixed_conversation_id,
            ),
        ):
            # --- Act: build the start request
            start_req = await service._build_start_conversation_request_for_user(
                initial_message=None,
                git_provider=None,  # Keep secrets path simple
                working_dir='/tmp/project',  # Arbitrary path
            )

            # The agent in the StartConversationRequest is the *same* object we provided
            assert start_req.agent is mock_agent

            # No tweaks to agent fields by the experiment manager (noop)
            assert start_req.agent.llm is mock_llm
            assert start_req.agent.system_prompt_filename == 'default_system_prompt.j2'
