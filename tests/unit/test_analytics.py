import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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
    @patch('openhands.server.analytics.UserAnalytics.has_user_consented')
    def test_track_event(self, mock_has_consented, mock_posthog):
        # Setup
        analytics = UserAnalytics(self.mock_server_config)
        mock_has_consented.return_value = asyncio.Future()
        mock_has_consented.return_value.set_result(True)

        # Execute
        result = asyncio.run(
            analytics.track_event('user123', 'test_event', {'prop': 'value'})
        )

        # Assert
        self.assertTrue(result)
        mock_posthog.capture.assert_called_once_with(
            distinct_id='user123', event='test_event', properties={'prop': 'value'}
        )

    @patch('openhands.server.analytics.posthog')
    def test_track_event_no_user_id(self, mock_posthog):
        # Setup
        analytics = UserAnalytics(self.mock_server_config)

        # Execute
        result = asyncio.run(analytics.track_event('', 'test_event'))

        # Assert
        self.assertFalse(result)
        mock_posthog.capture.assert_not_called()

    @patch('openhands.server.analytics.posthog')
    @patch('openhands.server.analytics.UserAnalytics.has_user_consented')
    def test_track_event_no_consent(self, mock_has_consented, mock_posthog):
        # Setup
        analytics = UserAnalytics(self.mock_server_config)
        mock_has_consented.return_value = asyncio.Future()
        mock_has_consented.return_value.set_result(False)

        # Execute
        result = asyncio.run(analytics.track_event('user123', 'test_event'))

        # Assert
        self.assertFalse(result)
        mock_posthog.capture.assert_not_called()

    @patch('openhands.server.analytics.posthog')
    @patch('openhands.server.analytics.UserAnalytics.track_event')
    def test_track_conversation_created(self, mock_track_event, mock_posthog):
        # Setup
        analytics = UserAnalytics(self.mock_server_config)
        mock_track_event.return_value = asyncio.Future()
        mock_track_event.return_value.set_result(True)

        # Execute
        result = asyncio.run(
            analytics.track_conversation_created(
                'user123', 'conv456', True, False, True
            )
        )

        # Assert
        self.assertTrue(result)
        mock_track_event.assert_called_once_with(
            'user123',
            'conversation_created',
            {
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

    @patch('openhands.server.analytics.SettingsStoreImpl')
    async def test_has_user_consented(self, mock_settings_store):
        # Setup
        analytics = UserAnalytics(self.mock_server_config)
        mock_settings = MagicMock()
        mock_settings.user_consents_to_analytics = True

        mock_store_instance = AsyncMock()
        mock_store_instance.load.return_value = mock_settings

        mock_settings_store.get_instance.return_value = asyncio.Future()
        mock_settings_store.get_instance.return_value.set_result(mock_store_instance)

        # Execute
        result = await analytics.has_user_consented('user123')

        # Assert
        self.assertTrue(result)
        mock_settings_store.get_instance.assert_called_once()
        mock_store_instance.load.assert_called_once()


if __name__ == '__main__':
    unittest.main()
