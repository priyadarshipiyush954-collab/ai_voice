import speech_recognition as sr
import pyttsx3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time
from dotenv import load_dotenv

# 🔒 Load environment variables
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# 🎵 Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-modify-playback-state,user-read-playback-state"
))

# 🎙 Initialize Speech Recognition & TTS
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def listen_for_command():
    """Listen for a voice command."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.2)
        print("Listening...")

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized: {command}")
            return command
        except sr.WaitTimeoutError:
            print("No command detected. Try again.")
            return None
        except sr.UnknownValueError:
            print("Could not understand. Try again.")
            return None
        except sr.RequestError:
            print("Check your internet connection.")
            return None

def get_active_device():
    """Get the active Spotify device."""
    devices = sp.devices()
    if devices['devices']:
        return devices['devices'][0]['id']
    return None

def search_best_song(song_query):
    """Search for the most accurate song match on Spotify."""
    results = sp.search(q=f"track:{song_query}", type="track", limit=10)

    best_match = None
    highest_popularity = -1

    for track in results['tracks']['items']:
        song_title = track['name'].lower()
        artist_name = track['artists'][0]['name'].lower()

        if song_query in song_title or song_query in artist_name:
            # Select the most popular relevant track
            if track['popularity'] > highest_popularity:
                highest_popularity = track['popularity']
                best_match = track

    return best_match

def play_song_on_spotify(song_name):
    """Play the most accurate song match on Spotify."""
    best_match = search_best_song(song_name)

    if best_match:
        song_uri = best_match['uri']
        song_title = best_match['name']
        artist = best_match['artists'][0]['name']
        print(f"Playing: {song_title} by {artist} 🎵")

        # Get active device
        device_id = get_active_device()
        if not device_id:
            print("No active Spotify device found. Please open Spotify.")
            speak("Opening Spotify. Please wait.")
            os.system("start spotify")  # Open Spotify on Windows
            time.sleep(5)  # Wait for Spotify to start
            device_id = get_active_device()

        if device_id:
            sp.transfer_playback(device_id, force_play=True)  # 🔥 Force playback on active device
            time.sleep(2)  # 🔄 UI refresh delay
            sp.start_playback(device_id=device_id, uris=[song_uri])
            auto_play_next_song(device_id)  # Auto-play next song
        else:
            print("Still no active device found.")
            speak("Please open Spotify on one of your devices.")
    else:
        print("Song not found!")
        speak("I couldn't find that song.")

def auto_play_next_song(device_id):
    """Automatically play the next song after the current one finishes."""
    while True:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            progress = playback['progress_ms']
            duration = playback['item']['duration_ms']

            if progress and duration and (duration - progress) < 5000:  # 5 seconds before end
                print("Playing next song... 🎵")
                sp.next_track(device_id=device_id)
                time.sleep(5)  # Allow time for track to change
        else:
            break
        time.sleep(1)

def main():
    """Main function to handle voice commands."""
    speak("Hello, say 'Ether' to wake me up.")

    while True:
        wake_word = listen_for_command()
        if wake_word and "ether" in wake_word:
            speak("Yes? What song do you want to play?")
            song_request = listen_for_command()
            if song_request:
                if "stop" in song_request:
                    speak("Goodbye!")
                    break
                play_song_on_spotify(song_request)

if __name__ == "__main__":
    main()
