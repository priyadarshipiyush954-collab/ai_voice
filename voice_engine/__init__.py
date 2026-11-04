"""
Voice Engine Package for Ether AI Voice Assistant.
Offline-capable local voice and AI engine. Includes:
- Faster-Whisper Speech Recognition (local only, no cloud fallback)
- Voice Profile Training & Speaker Verification (local MFCC)
- Local LLM Provider Interface (Ollama / Llama.cpp)
- Offline Question Answering (local LLM synthesis)
- Thread-Safe Text-to-Speech Engine (pyttsx3, no cloud TTS)
"""
__version__ = "2.0.0-offline"
