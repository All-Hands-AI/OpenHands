from openhands.cartesia_tts import CartesiaTTS

def enable_tts():
    """Enable text-to-speech for agent messages"""
    tts = CartesiaTTS()
    tts.enable()
    print("Text-to-speech enabled. The agent will now speak its messages.")

def disable_tts():
    """Disable text-to-speech for agent messages"""
    tts = CartesiaTTS()
    tts.disable()
    print("Text-to-speech disabled. The agent will no longer speak its messages.")

def list_voices():
    """List available voices for text-to-speech"""
    tts = CartesiaTTS()
    voices = tts.list_voices()
    print("\nAvailable voices:")
    for voice in voices:
        print(f"ID: {voice['id']}")
        print(f"Name: {voice['name']}")
        print(f"Description: {voice.get('description', 'No description')}")
        print("-" * 40)

def set_voice(voice_id: str):
    """Set the voice to use for text-to-speech
    
    Args:
        voice_id (str): The ID of the voice to use
    """
    tts = CartesiaTTS()
    tts.set_voice(voice_id)
    print(f"Voice set to: {voice_id}")