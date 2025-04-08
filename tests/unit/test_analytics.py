import unittest
from unittest.mock import MagicMock, patch

from openhands.server.analytics import UserAnalytics
from openhands.server.config.server_config import ServerConfig


class TestUserAnalytics(unittest.TestCase):
    def setUp(self):
        self.mock_server_config = MagicMock(spec=ServerConfig)
        self.mock_server_config.posthog_client_key = 'test_key'

    @patch('openhands.server.analytics.posthog')
    def test_initialization(self, mock_posthog):
        analytics = UserAnalytics(self.mock_server_config)
        self.assertTrue(analytics.initialized)
        mock_posthog.api_key = 'test_key'

    @patch('openhands.server.analytics.posthog')
    def test_track_event(self, mock_posthog):
        analytics = UserAnalytics(self.mock_server_config)
        result = analytics.track_event('user123', 'test_event', {'prop': 'value'})
        self.assertTrue(result)
        mock_posthog.capture.assert_called_once_with(
            distinct_id='user123', event='test_event', properties={'prop': 'value'}
        )

    @patch('openhands.server.analytics.posthog')
    def test_track_event_no_user_id(self, mock_posthog):
        analytics = UserAnalytics(self.mock_server_config)
        result = analytics.track_event('', 'test_event')
        self.assertFalse(result)
        mock_posthog.capture.assert_not_called()

    @patch('openhands.server.analytics.posthog')
    def test_track_conversation_created(self, mock_posthog):
        analytics = UserAnalytics(self.mock_server_config)
        result = analytics.track_conversation_created(
            'user123', 'conv456', True, False, True
        )
        self.assertTrue(result)
        mock_posthog.capture.assert_called_once_with(
            distinct_id='user123',
            event='conversation_created',
            properties={
                'conversation_id': 'conv456',
                'has_initial_message': True,
                'has_repository': False,
                'has_images': True,
            },
        )

    @patch('openhands.server.analytics.posthog')
    def test_singleton_pattern(self, mock_posthog):
        analytics1 = UserAnalytics.get_instance(self.mock_server_config)
        analytics2 = UserAnalytics.get_instance(self.mock_server_config)
        self.assertIs(analytics1, analytics2)


if __name__ == '__main__':
    unittest.main()
