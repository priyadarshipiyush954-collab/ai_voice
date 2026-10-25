import os
import threading
import logging
import queue
from typing import Optional

logger = logging.getLogger("TTS")

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


class TextToSpeech:
    """
    Thread-Safe Text-To-Speech engine with queueing and speech controls.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self.speech_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def _speech_worker(self):
        """Worker thread executing speech to avoid blocking async loops."""
        engine = None
        if HAS_PYTTSX3:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
            except Exception as e:
                logger.warning(f"Could not initialize pyttsx3 in worker thread: {e}")

        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            try:
                if engine:
                    engine.say(text)
                    engine.runAndWait()
                else:
                    # Windows PowerShell SAPI fallback
                    clean = text.replace('"', '\\"').replace("'", "")
                    os.system(f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean}\')" >nul 2>&1')
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
            finally:
                self.speech_queue.task_done()

    def speak(self, text: str, block: bool = False):
        """Queue text for speaking."""
        if not text:
            return
        logger.info(f"Speaking: '{text}'")
        self.speech_queue.put(text)
        if block:
            self.speech_queue.join()
