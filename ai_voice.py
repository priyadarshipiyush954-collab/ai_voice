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
from voice_engine.spotify_controller import SpotifyController
from voice_engine.tts import TextToSpeech

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EtherVoice")

# Initialize modules
recognizer = HighAccuracyRecognizer(engine_type="whisper", model_size="base.en")
voice_trainer = VoiceTrainer()
web_analyzer = WebAnalyzer()
spotify = SpotifyController()
tts = TextToSpeech()


def speak(text: str, block: bool = True):
    """Speak text through Text-to-Speech."""
    print(f"\n🎙 [Ether]: {text}")
    tts.speak(text, block=block)


def handle_user_command(command: str):
    """
    Intelligent Command Dispatcher:
    - Spotify Media Control
    - Web Analysis & Search
    - Assistant Controls
    """
    cmd = command.lower().strip()
    logger.info(f"Dispatching command: '{cmd}'")

    # 1. Stop / Goodbye
    if any(k in cmd for k in ["stop listening", "goodbye", "exit", "shutdown"]):
        speak("Goodbye! Have a great day.")
        return False

    # 2. Spotify Music Playback
    if cmd.startswith("play ") or "play song" in cmd or "on spotify" in cmd:
        song_query = cmd.replace("play song", "").replace("play", "").replace("on spotify", "").strip()
        if not song_query:
            speak("What song would you like me to play?")
            return True

        speak(f"Searching Spotify for {song_query}...")
        res = spotify.search_and_play(song_query)
        if res["success"]:
            speak(f"Now playing {res['track_name']} by {res['artist']}")
        else:
            speak(res["message"])
        return True

    # 3. Spotify Control (Pause, Resume, Next, Previous)
    if "pause music" in cmd or cmd == "pause":
        spotify.pause()
        speak("Music paused.")
        return True

    if "resume music" in cmd or cmd == "resume":
        spotify.resume()
        speak("Music resumed.")
        return True

    if "next song" in cmd or cmd == "skip":
        spotify.next_track()
        speak("Skipping to next track.")
        return True

    # 4. Web Analysis & Deep Research
    if any(cmd.startswith(prefix) for prefix in ["analyze", "search", "what is", "who is", "tell me about", "latest news"]):
        # Extract core topic
        topic = cmd
        for prefix in ["analyze the web for", "analyze", "search the web for", "search for", "search", "tell me about", "what is", "who is"]:
            if topic.startswith(prefix):
                topic = topic[len(prefix):].strip()
                break

        speak(f"Analyzing the web for {topic}...")
        analysis = web_analyzer.analyze_web(topic)
        
        # Speak the concise executive summary
        summary = analysis.get("spoken_summary", "I found some results on the web.")
        speak(summary)

        # Print detailed takeaways in console
        takeaways = analysis.get("key_takeaways", [])
        if takeaways:
            print("\n📋 Key Takeaways:")
            for item in takeaways:
                print(f"  • {item}")

        sources = analysis.get("sources", [])
        if sources:
            print("\n🔗 Top Sources:")
            for s in sources[:3]:
                print(f"  - {s['title']} ({s['url']})")
        return True

    # 5. Default Fallback -> Web Search
    speak(f"Let me look up {cmd} on the web.")
    analysis = web_analyzer.analyze_web(cmd)
    speak(analysis.get("spoken_summary", "Here is what I found."))
    return True


def run_voice_loop():
    """Continuous microphone listening loop with wake-word detection."""
    print("=" * 65)
    print("   🎙 ETHER AI VOICE ASSISTANT - HIGH ACCURACY ENGINE")
    print(f"   Model: {recognizer.model_size} ({recognizer.engine_type})")
    print(f"   Active Voice Profile: {voice_trainer.active_profile or 'None (Open mode)'}")
    print("   Say 'Ether' to wake up.")
    print("=" * 65)

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
