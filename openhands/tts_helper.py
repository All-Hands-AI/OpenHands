import pyttsx3
import threading

class TTSHelper:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TTSHelper, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if not self._initialized:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.enabled = False
            self._initialized = True

    def speak(self, text):
        if self.enabled:
            self.engine.say(text)
            self.engine.runAndWait()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def is_enabled(self):
        return self.enabled