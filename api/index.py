import os
import sys
import json
import logging
from typing import Optional, List

# Ensure parent directory is in sys.path for Vercel serverless environment
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Import voice engine modules
from voice_engine.web_analyzer import WebAnalyzer
from voice_engine.voice_trainer import VoiceTrainer
from voice_engine.spotify_controller import SpotifyController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VercelEther")

app = FastAPI(
    title="Ether AI Voice - Serverless Edition",
    description="High-Accuracy Voice AI, Web Analysis, and Spotify Hub on Vercel",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files path
WEB_DIR = os.path.join(PARENT_DIR, "web")
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# Instantiate engines
web_analyzer = WebAnalyzer()
voice_trainer = VoiceTrainer(profiles_dir=os.path.join("/tmp", "voice_profiles") if not os.access(PARENT_DIR, os.W_OK) else None)
spotify_controller = SpotifyController()


class QueryRequest(BaseModel):
    query: str

class SpeakRequest(BaseModel):
    text: str

class SettingsRequest(BaseModel):
    engine: str
    whisper_model: Optional[str] = "base.en"
    energy_threshold: Optional[int] = 400
    wake_sensitivity: Optional[int] = 80


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Ether AI Voice Assistant</h1><p>Online on Vercel.</p>")


@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "environment": "vercel-serverless",
        "engine": "browser-speech-api + cloud-speech",
        "active_profile": voice_trainer.active_profile,
        "spotify_configured": spotify_controller.is_configured
    }


@app.post("/api/analyze-web")
async def analyze_web(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return web_analyzer.analyze_web(req.query.strip())


@app.get("/api/voice-profiles")
async def list_profiles():
    return {
        "profiles": voice_trainer.list_profiles(),
        "active": voice_trainer.active_profile
    }


@app.post("/api/train-voice")
async def train_voice(
    speaker_name: str = Form(...),
    samples: List[UploadFile] = File(...)
):
    if not samples:
        raise HTTPException(status_code=400, detail="No audio samples provided")

    audio_bytes_list = []
    for s in samples:
        content = await s.read()
        if content:
            audio_bytes_list.append(content)

    return voice_trainer.train_profile(speaker_name, audio_bytes_list)


@app.post("/api/verify-voice")
async def verify_voice(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")
    return voice_trainer.verify_voice(audio_bytes)


@app.post("/api/spotify/play")
async def spotify_play(req: QueryRequest):
    return spotify_controller.search_and_play(req.query.strip())


@app.post("/api/spotify/pause")
async def spotify_pause():
    return spotify_controller.pause()


@app.post("/api/spotify/next")
async def spotify_next():
    return spotify_controller.next_track()


@app.post("/api/spotify/previous")
async def spotify_previous():
    return spotify_controller.previous_track()


@app.get("/api/spotify/status")
async def spotify_status():
    return spotify_controller.get_status()


@app.post("/api/calibrate-noise")
async def calibrate_noise():
    return {"energy_threshold": 400, "note": "Browser Web Audio calibration active"}


@app.post("/api/settings")
async def update_settings(settings: SettingsRequest):
    return {
        "success": True,
        "engine": settings.engine,
        "model": settings.whisper_model,
        "energy_threshold": settings.energy_threshold
    }


@app.post("/api/speak")
async def speak_text(req: SpeakRequest):
    return {"success": True, "method": "browser-speech-synthesis"}


# Standard Vercel handler export
app_handler = app
