import os
import unittest
from unittest.mock import patch, MagicMock
import json
from openhands.cartesia_tts import CartesiaTTS

class TestCartesiaTTS(unittest.TestCase):
    def setUp(self):
        # Mock environment variable
        self.api_key = "test_api_key"
        os.environ['CARTESIA_API_KEY'] = self.api_key
        
        # Create TTS instance
        self.tts = CartesiaTTS()
        
        # Sample voice data
        self.sample_voice = {
            "id": "test-voice-id",
            "name": "Test Voice",
            "description": "A test voice"
        }
        
        # Sample audio data
        self.sample_audio_event = {
            "type": "chunk",
            "chunk": "base64_encoded_audio_data"
        }
        
        self.sample_done_event = {
            "type": "done"
        }

    def tearDown(self):
        # Clean up environment
        if 'CARTESIA_API_KEY' in os.environ:
            del os.environ['CARTESIA_API_KEY']

    def test_singleton_pattern(self):
        """Test that CartesiaTTS follows the singleton pattern"""
        tts1 = CartesiaTTS()
        tts2 = CartesiaTTS()
        self.assertIs(tts1, tts2)

    def test_enable_disable(self):
        """Test enabling and disabling TTS"""
        self.tts.enable()
        self.assertTrue(self.tts.is_enabled())
        
        self.tts.disable()
        self.assertFalse(self.tts.is_enabled())

    @patch('requests.get')
    def test_list_voices(self, mock_get):
        """Test listing available voices"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [self.sample_voice]
        mock_get.return_value = mock_response
        
        voices = self.tts.list_voices()
        
        # Verify the request
        mock_get.assert_called_once_with(
            f"{self.tts.base_url}/voices",
            headers={
                'X-API-Key': self.api_key,
                'Cartesia-Version': '2024-06-10'
            }
        )
        
        # Verify the response
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]['id'], self.sample_voice['id'])

    def test_set_voice(self):
        """Test setting voice ID"""
        voice_id = "test-voice-id"
        self.tts.set_voice(voice_id)
        self.assertEqual(self.tts.voice_id, voice_id)

    @patch('requests.post')
    @patch('sseclient.SSEClient')
    def test_get_speech_data(self, mock_sse_client, mock_post):
        """Test text-to-speech conversion to data URL"""
        # Enable TTS and set voice
        self.tts.enable()
        self.tts.set_voice("test-voice-id")
        
        # Mock SSE events
        mock_event1 = MagicMock()
        mock_event1.data = json.dumps(self.sample_audio_event)
        mock_event2 = MagicMock()
        mock_event2.data = json.dumps(self.sample_done_event)
        
        mock_sse_client.return_value.events.return_value = [mock_event1, mock_event2]
        
        # Test getting speech data
        test_text = "Hello, world!"
        result = self.tts.get_speech_data(test_text)
        
        # Verify the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # Check URL
        self.assertEqual(args[0], f"{self.tts.base_url}/tts/sse")
        
        # Check headers
        self.assertEqual(kwargs['headers']['X-API-Key'], self.api_key)
        self.assertEqual(kwargs['headers']['Cartesia-Version'], '2024-06-10')
        
        # Check request body
        self.assertEqual(kwargs['json']['transcript'], test_text)
        self.assertEqual(kwargs['json']['voice']['id'], "test-voice-id")
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIn('audio_url', result)
        self.assertIn('sample_rate', result)
        self.assertIn('format', result)
        self.assertTrue(result['audio_url'].startswith('data:audio/wav;base64,'))
        self.assertEqual(result['format']['container'], 'wav')

    def test_get_speech_data_when_disabled(self):
        """Test that get_speech_data returns None when TTS is disabled"""
        self.tts.disable()
        result = self.tts.get_speech_data("Hello")
        self.assertIsNone(result)

    def test_get_speech_data_without_voice(self):
        """Test that get_speech_data returns None when no voice is set"""
        self.tts.enable()
        result = self.tts.get_speech_data("Hello")
        self.assertIsNone(result)

    def test_missing_api_key(self):
        """Test that initialization fails without API key"""
        if 'CARTESIA_API_KEY' in os.environ:
            del os.environ['CARTESIA_API_KEY']
        
        with self.assertRaises(ValueError):
            CartesiaTTS()