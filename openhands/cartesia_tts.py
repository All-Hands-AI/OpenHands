import os
import json
import threading
import requests
import sseclient
import base64
from typing import Optional, Dict, Any

class CartesiaTTS:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CartesiaTTS, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.api_key = os.getenv('CARTESIA_API_KEY')
            if not self.api_key:
                raise ValueError("CARTESIA_API_KEY environment variable not set")
            
            self.base_url = "https://api.cartesia.ai"
            self.enabled = False
            self.voice_id = None  # Will be set when a voice is selected
            self.sample_rate = 44100
            self._initialized = True
    
    def list_voices(self):
        """Get list of available voices from Cartesia API"""
        headers = {
            'X-API-Key': self.api_key,
            'Cartesia-Version': '2024-06-10'
        }
        response = requests.get(f"{self.base_url}/voices", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def set_voice(self, voice_id: str):
        """Set the voice to use for TTS"""
        self.voice_id = voice_id
    
    def get_speech_data(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Convert text to speech and return audio data for frontend playback
        
        Returns:
            Dict containing:
            - audio_url: Data URL containing the audio data
            - sample_rate: Sample rate of the audio
            - format: Audio format information
        """
        if not self.enabled or not self.voice_id:
            return None
            
        headers = {
            'X-API-Key': self.api_key,
            'Cartesia-Version': '2024-06-10',
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model_id": "sonic-english",
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": self.voice_id
            },
            "output_format": {
                "container": "wav",  # Changed to WAV for browser compatibility
                "encoding": "pcm_f32le",
                "sample_rate": self.sample_rate
            },
            "language": language
        }
        
        response = requests.post(
            f"{self.base_url}/tts/sse",
            headers=headers,
            json=data,
            stream=True
        )
        
        client = sseclient.SSEClient(response)
        audio_chunks = []
        
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data.get("type") == "chunk":
                        # Collect base64 audio chunks
                        audio_chunks.append(data["chunk"])
                    elif data.get("type") == "done":
                        break
                except json.JSONDecodeError:
                    continue
        
        if audio_chunks:
            # Combine chunks and create data URL
            audio_data = ''.join(audio_chunks)
            audio_url = f"data:audio/wav;base64,{audio_data}"
            
            return {
                "audio_url": audio_url,
                "sample_rate": self.sample_rate,
                "format": {
                    "container": "wav",
                    "encoding": "pcm_f32le"
                }
            }
        
        return None
    
    def enable(self):
        """Enable TTS functionality"""
        self.enabled = True
    
    def disable(self):
        """Disable TTS functionality"""
        self.enabled = False
    
    def is_enabled(self):
        """Check if TTS is enabled"""
        return self.enabled