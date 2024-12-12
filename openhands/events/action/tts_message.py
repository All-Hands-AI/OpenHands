from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from openhands.events.action.message import MessageAction
from openhands.cartesia_tts import CartesiaTTS

@dataclass
class TTSMessageAction(MessageAction):
    speech_data: Optional[Dict[str, Any]] = field(default=None, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        # Initialize TTS when first message is sent
        try:
            tts = CartesiaTTS()
            if tts.is_enabled():
                self.speech_data = tts.get_speech_data(self.content)
        except Exception as e:
            # Log error but don't stop message delivery
            print(f"TTS Error: {str(e)}")
            self.speech_data = None