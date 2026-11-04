"""
Ether AI Voice Assistant - Core CLI & Voice Daemon
Upgraded with:
- High-Accuracy Speech Recognition (OpenAI Whisper + Google Speech)
- Speaker Profile Verification ("Train with Voices")
- Deep Web Analysis & AI Summarization
- Spotify Media Control
- Dual Web UI & CLI Execution
"""

import os
import sys
import time
import argparse
import threading
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import engine submodules
from voice_engine.recognizer import HighAccuracyRecognizer
from voice_engine.voice_trainer import VoiceTrainer
from voice_engine.web_analyzer import WebAnalyzer
from voice_engine.llm_provider import LLMProvider
from voice_engine.tts import TextToSpeech

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EtherVoice")

# Initialize modules
recognizer = HighAccuracyRecognizer(engine_type="whisper", model_size="base.en")
voice_trainer = VoiceTrainer()
llm_provider = LLMProvider(
    provider=os.getenv("LLM_PROVIDER", "ollama"),
    model_name=os.getenv("LLM_MODEL", "neural-chat"),
    endpoint=os.getenv("LLM_ENDPOINT", "http://localhost:11434")
)
web_analyzer = WebAnalyzer(llm_provider=llm_provider)
tts = TextToSpeech()


def speak(text: str, block: bool = True):
    """Speak text through Text-to-Speech."""
    print(f"\n🎙 [Ether]: {text}")
    tts.speak(text, block=block)


def handle_user_command(command: str):
    """
    Intelligent Command Dispatcher:
    - Local LLM Question Answering
    - Assistant Controls
    """
    cmd = command.lower().strip()
    logger.info(f"Dispatching command: '{cmd}'")

    # 1. Stop / Goodbye
    if any(k in cmd for k in ["stop listening", "goodbye", "exit", "shutdown"]):
        speak("Goodbye! Have a great day.")
        return False

    # 2. Question Answering with Local LLM
    if any(cmd.startswith(prefix) for prefix in ["what is", "who is", "tell me about", "explain", "how does"]):
        # Extract core topic
        topic = cmd
        for prefix in ["tell me about", "what is", "who is", "explain", "how does"]:
            if topic.startswith(prefix):
                topic = topic[len(prefix):].strip()
                break

        speak(f"Let me think about {topic}...")
        analysis = web_analyzer.analyze_web(topic)

        # Speak the response
        summary = analysis.get("spoken_summary", "I couldn't generate a response.")
        speak(summary)

        # Print status in console
        if analysis.get("offline_mode"):
            print(f"\n💡 Offline Mode: Response from local LLM")
            print(f"   Model: {analysis.get('model', 'N/A')}")

        takeaways = analysis.get("key_takeaways", [])
        if takeaways:
            print("\n📋 Notes:")
            for item in takeaways:
                print(f"  • {item}")
        return True

    # 3. Default Fallback -> Try LLM
    speak("Let me answer that for you.")
    analysis = web_analyzer.analyze_web(cmd)
    speak(analysis.get("spoken_summary", "I couldn't process that request."))
    return True


def run_voice_loop():
    """Continuous microphone listening loop with wake-word detection."""
    # Check local LLM availability and display status
llm_status_msg = "LLM: Not configured" if not llm_provider.is_available else f"LLM: {llm_provider.model_name}"
if llm_provider.is_available:
    try:
        # Quick health check
        status = llm_provider.get_status()
        if status.get("error"):
            llm_status_msg = f"LLM: Error - {status['error'][:50]}"
    except:
        llm_status_msg = "LLM: Connecting..."

print("=" * 70)
print("   🎙 ETHER AI VOICE ASSISTANT - OFFLINE-CAPABLE")
print(f"   Whisper Model: {recognizer.model_size} ({recognizer.engine_type})")
print(f"   Active Voice Profile: {voice_trainer.active_profile or 'None (Open mode)'}")
print(f"   {llm_status_msg}")
print(f"   Offline Mode: {'Enabled' if llm_provider.is_available else 'Limited - configure LLM for Q&A'}")
print("   Say 'Ether' to wake up.")
print("=" * 70)

    # Ambient noise calibration
    print("\n[Calibrating ambient noise floor...]")
    recognizer.calibrate_noise(duration=1.0)
    speak("Hello! Say 'Ether' to wake me up.")

    while True:
        try:
            print("\n[Listening for wake word 'Ether'...]")
            result = recognizer.listen_from_mic(timeout=5, phrase_time_limit=6)
            transcript = result.get("text", "").lower()

            if not transcript:
                continue

            print(f"Heard: '{transcript}' (Confidence: {result.get('confidence', 0):.0%})")

            # Check for wake word
            if "ether" in transcript or "either" in transcript or "aether" in transcript:
                speak("Yes? How can I help you?")

                # Listen for the actual command
                cmd_res = recognizer.listen_from_mic(timeout=6, phrase_time_limit=8)
                cmd_text = cmd_res.get("text", "").strip()

                if cmd_text:
                    print(f"Command recognized: '{cmd_text}'")
                    keep_going = handle_user_command(cmd_text)
                    if not keep_going:
                        break
                else:
                    speak("I didn't catch that. Please try again.")

        except KeyboardInterrupt:
            print("\nExiting voice loop.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(1)


def start_web_server(port: int = 8000):
    """Start the FastAPI Web UI server."""
    import uvicorn
    from app import app
    print(f"\n🌐 Launching Ether AI Voice Web Interface on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="Ether AI Voice Assistant")
    parser.add_argument("--web", action="store_true", help="Launch the Web UI interface")
    parser.add_argument("--cli", action="store_true", help="Run in terminal voice-only mode")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")
    parser.add_argument("--model", type=str, default="base.en", help="Whisper model weight (tiny.en, base.en, small.en)")
    args = parser.parse_args()

    recognizer.set_engine("whisper", args.model)

    if args.cli:
        run_voice_loop()
    elif args.web:
        start_web_server(args.port)
    else:
        # Default: Start Web UI in main thread or spawn voice loop in background
        print("\nStarting Ether AI Voice (Web Interface + Voice Engine)")
        start_web_server(args.port)


if __name__ == "__main__":
    main()
