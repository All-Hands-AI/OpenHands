from unittest.mock import MagicMock

from openhands.events.action.agent import RecallAction
from openhands.events.event import RecallType
from openhands.events.observation.agent import RecallObservation
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory


class TestRepositoryInfo:
    def test_set_repository_info_with_url(self):
        """Test that set_repository_info sets the repo_url field."""
        file_store = MagicMock()
        event_stream = EventStream('test_sid', file_store)
        memory = Memory(event_stream=event_stream, sid='test_sid')

        # Test with a GitHub repository
        repo_name = 'All-Hands-AI/OpenHands'
        repo_directory = '/workspace/OpenHands'
        memory.set_repository_info(repo_name, repo_directory)

        assert memory.repository_info is not None
        assert memory.repository_info.repo_name == repo_name
        assert memory.repository_info.repo_directory == repo_directory
        assert (
            memory.repository_info.repo_url
            == 'https://github.com/All-Hands-AI/OpenHands'
        )

        # Test with a custom repository URL
        repo_url = 'https://github.com/All-Hands-AI/OpenHands.git'
        memory.set_repository_info(repo_name, repo_directory, repo_url)

        assert memory.repository_info is not None
        assert memory.repository_info.repo_name == repo_name
        assert memory.repository_info.repo_directory == repo_directory
        assert memory.repository_info.repo_url == repo_url

    def test_workspace_context_recall_includes_repo_url(self):
        """Test that workspace context recall includes the repo_url field."""
        file_store = MagicMock()
        event_stream = EventStream('test_sid', file_store)
        memory = Memory(event_stream=event_stream, sid='test_sid')

        # Set repository info
        repo_name = 'All-Hands-AI/OpenHands'
        repo_directory = '/workspace/OpenHands'
        repo_url = 'https://github.com/All-Hands-AI/OpenHands.git'
        memory.set_repository_info(repo_name, repo_directory, repo_url)

        # Create a recall action
        recall_action = RecallAction(
            recall_type=RecallType.WORKSPACE_CONTEXT,
            query='',
        )

        # Process the recall action
        observation = memory._on_workspace_context_recall(recall_action)

        assert isinstance(observation, RecallObservation)
        assert observation.repo_name == repo_name
        assert observation.repo_directory == repo_directory
        assert observation.repo_url == repo_url

