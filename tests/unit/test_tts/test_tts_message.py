import unittest
from unittest.mock import patch, MagicMock
from openhands.events.action.tts_message import TTSMessageAction
from openhands.cartesia_tts import CartesiaTTS
from openhands.events import EventSource

class TestTTSMessageAction(unittest.TestCase):
    def setUp(self):
        # Create a mock CartesiaTTS instance
        self.mock_tts = MagicMock(spec=CartesiaTTS)
        self.mock_tts.is_enabled.return_value = True
        
        # Sample speech data
        self.sample_speech_data = {
            "audio_url": "data:audio/wav;base64,test_audio_data",
            "sample_rate": 44100,
            "format": {
                "container": "wav",
                "encoding": "pcm_f32le"
            }
        }
        
    @patch('openhands.events.action.tts_message.CartesiaTTS')
    def test_message_with_tts_enabled(self, mock_cartesia_class):
        """Test that TTS data is included when enabled"""
        # Setup mock
        self.mock_tts.get_speech_data.return_value = self.sample_speech_data
        mock_cartesia_class.return_value = self.mock_tts
        
        # Create message action
        test_content = "Hello, world!"
        message = TTSMessageAction(
            content=test_content,
            source=EventSource.AGENT
        )
        
        # Verify TTS was called and data was stored
        self.mock_tts.get_speech_data.assert_called_once_with(test_content)
        self.assertEqual(message.speech_data, self.sample_speech_data)
    
    @patch('openhands.events.action.tts_message.CartesiaTTS')
    def test_message_with_tts_disabled(self, mock_cartesia_class):
        """Test that TTS data is not included when disabled"""
        # Setup mock to return disabled
        self.mock_tts.is_enabled.return_value = False
        mock_cartesia_class.return_value = self.mock_tts
        
        # Create message action
        message = TTSMessageAction(
            content="Hello, world!",
            source=EventSource.AGENT
        )
        
        # Verify TTS was not called and no data was stored
        self.mock_tts.get_speech_data.assert_not_called()
        self.assertIsNone(message.speech_data)
    
    @patch('openhands.events.action.tts_message.CartesiaTTS')
    def test_message_with_tts_error(self, mock_cartesia_class):
        """Test that message creation succeeds even if TTS fails"""
        # Setup mock to raise an exception
        self.mock_tts.get_speech_data.side_effect = Exception("TTS Error")
        mock_cartesia_class.return_value = self.mock_tts
        
        # This should not raise an exception
        message = TTSMessageAction(
            content="Hello, world!",
            source=EventSource.AGENT
        )
        
        # Verify message was created successfully without speech data
        self.assertEqual(message.content, "Hello, world!")
        self.assertEqual(message.source, EventSource.AGENT)
        self.assertIsNone(message.speech_data)

    def test_message_properties(self):
        """Test that TTSMessageAction maintains MessageAction properties"""
        content = "Test message"
        image_urls = ["http://example.com/image.jpg"]
        wait_for_response = True
        
        message = TTSMessageAction(
            content=content,
            image_urls=image_urls,
            wait_for_response=wait_for_response,
            source=EventSource.AGENT
        )
        
        self.assertEqual(message.content, content)
        self.assertEqual(message.message, content)  # Test alias property
        self.assertEqual(message.image_urls, image_urls)
        self.assertEqual(message.wait_for_response, wait_for_response)
        self.assertEqual(message.source, EventSource.AGENT)