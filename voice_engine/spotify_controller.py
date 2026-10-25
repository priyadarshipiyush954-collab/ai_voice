import os
import time
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("SpotifyController")

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    HAS_SPOTIPY = True
except ImportError:
    HAS_SPOTIPY = False


class SpotifyController:
    """
    Enhanced Spotify Media Controller with safe fallback,
    rich track metadata, volume control, and playback management.
    """

    def __init__(self):
        self.client_id = os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
        self.sp = None
        self.is_configured = False

        if HAS_SPOTIPY and self.client_id and self.client_secret:
            try:
                self.sp = spotipy.Spotify(
                    auth_manager=SpotifyOAuth(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        redirect_uri=self.redirect_uri,
                        scope="user-modify-playback-state,user-read-playback-state,user-read-currently-playing"
                    )
                )
                self.is_configured = True
                logger.info("Spotify client authenticated successfully.")
            except Exception as e:
                logger.warning(f"Spotify authentication failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current playback status, active device, and song metadata."""
        if not self.is_configured or not self.sp:
            return {
                "configured": False,
                "is_playing": False,
                "track": None,
                "message": "Spotify credentials not set in .env"
            }

        try:
            playback = self.sp.current_playback()
            if playback and playback.get("item"):
                item = playback["item"]
                album_art = ""
                if item.get("album") and item["album"].get("images"):
                    album_art = item["album"]["images"][0]["url"]

                return {
                    "configured": True,
                    "is_playing": playback.get("is_playing", False),
                    "device": playback.get("device", {}).get("name", "Unknown Device"),
                    "track": {
                        "name": item.get("name"),
                        "artist": ", ".join([a["name"] for a in item.get("artists", [])]),
                        "album": item.get("album", {}).get("name"),
                        "album_art": album_art,
                        "duration_ms": item.get("duration_ms", 0),
                        "progress_ms": playback.get("progress_ms", 0),
                        "uri": item.get("uri")
                    }
                }
            return {
                "configured": True,
                "is_playing": False,
                "track": None,
                "message": "No active playback"
            }
        except Exception as e:
            return {"configured": True, "is_playing": False, "track": None, "error": str(e)}

    def search_and_play(self, query: str) -> Dict[str, Any]:
        """Search Spotify for the most accurate track match and trigger playback."""
        if not self.is_configured or not self.sp:
            return {
                "success": False,
                "message": "Spotify credentials not configured in .env (SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)"
            }

        try:
            results = self.sp.search(q=query, type="track", limit=10)
            items = results.get("tracks", {}).get("items", [])
            if not items:
                return {"success": False, "message": f"No tracks found matching '{query}'"}

            # Choose highest popularity track matching the query
            best_track = items[0]
            highest_pop = -1
            q_clean = query.lower()

            for track in items:
                t_title = track["name"].lower()
                a_name = track["artists"][0]["name"].lower() if track.get("artists") else ""
                pop = track.get("popularity", 0)

                if (q_clean in t_title or q_clean in a_name) and pop > highest_pop:
                    highest_pop = pop
                    best_track = track

            track_name = best_track["name"]
            artist_name = best_track["artists"][0]["name"] if best_track.get("artists") else "Unknown"
            uri = best_track["uri"]
            album_art = best_track["album"]["images"][0]["url"] if best_track.get("album", {}).get("images") else ""

            # Check active device
            devices = self.sp.devices().get("devices", [])
            device_id = devices[0]["id"] if devices else None

            if not device_id:
                os.system("start spotify")
                time.sleep(3)
                devices = self.sp.devices().get("devices", [])
                device_id = devices[0]["id"] if devices else None

            if device_id:
                self.sp.start_playback(device_id=device_id, uris=[uri])
                return {
                    "success": True,
                    "track_name": track_name,
                    "artist": artist_name,
                    "album_art": album_art,
                    "uri": uri,
                    "message": f"Playing {track_name} by {artist_name}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Found '{track_name}', but no active Spotify device found. Please launch Spotify."
                }
        except Exception as e:
            logger.error(f"Error playing song on Spotify: {e}")
            return {"success": False, "message": str(e)}

    def pause(self) -> Dict[str, Any]:
        """Pause playback."""
        if not self.is_configured or not self.sp:
            return {"success": False, "message": "Spotify not configured"}
        try:
            self.sp.pause_playback()
            return {"success": True, "message": "Playback paused"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def resume(self) -> Dict[str, Any]:
        """Resume playback."""
        if not self.is_configured or not self.sp:
            return {"success": False, "message": "Spotify not configured"}
        try:
            self.sp.start_playback()
            return {"success": True, "message": "Playback resumed"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def next_track(self) -> Dict[str, Any]:
        """Skip to next track."""
        if not self.is_configured or not self.sp:
            return {"success": False, "message": "Spotify not configured"}
        try:
            self.sp.next_track()
            return {"success": True, "message": "Skipped to next track"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def previous_track(self) -> Dict[str, Any]:
        """Go to previous track."""
        if not self.is_configured or not self.sp:
            return {"success": False, "message": "Spotify not configured"}
        try:
            self.sp.previous_track()
            return {"success": True, "message": "Playing previous track"}
        except Exception as e:
            return {"success": False, "message": str(e)}
