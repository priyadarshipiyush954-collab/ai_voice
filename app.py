import os
import io
import logging
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize Voice Engine submodules
from voice_engine.recognizer import HighAccuracyRecognizer
from voice_engine.voice_trainer import VoiceTrainer
from voice_engine.web_analyzer import WebAnalyzer
from voice_engine.llm_provider import LLMProvider
from voice_engine.tts import TextToSpeech

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("EtherApp")

app = FastAPI(
    title="Ether AI Voice Assistant",
    description="High-Accuracy Voice Recognition, Speaker Profile Training, Deep Web Analysis & Spotify Media Control",
    version="2.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Web assets directory
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# Instantiate Engines
recognizer = HighAccuracyRecognizer(engine_type="whisper", model_size="base.en")
voice_trainer = VoiceTrainer()

# Initialize Local LLM Provider
llm_provider = LLMProvider(
    provider=os.getenv("LLM_PROVIDER", "ollama"),
    model_name=os.getenv("LLM_MODEL", "neural-chat"),
    endpoint=os.getenv("LLM_ENDPOINT", "http://localhost:11434"),
    timeout=int(os.getenv("LLM_TIMEOUT", "30"))
)

web_analyzer = WebAnalyzer(llm_provider=llm_provider)
tts = TextToSpeech()


# Request Schemas
class QueryRequest(BaseModel):
    query: str

class SpeakRequest(BaseModel):
    text: str

class SettingsRequest(BaseModel):
    engine: str
    whisper_model: Optional[str] = "base.en"
    energy_threshold: Optional[int] = 400
    wake_sensitivity: Optional[int] = 80

class LLMRenameRequest(BaseModel):
    provider: str  # "ollama", "llama_cpp", "none"
    model: str  # model name


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the modern Swiss Light-theme Web UI."""
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Ether AI Voice Assistant</h1><p>Web UI index.html not found.</p>")


@app.get("/api/status")
async def get_system_status():
    """Get system health, active model, and service status."""
    llm_status = llm_provider.get_status()
    return {
        "status": "online",
        "engine": recognizer.engine_type,
        "whisper_model": recognizer.model_size,
        "active_profile": voice_trainer.active_profile,
        "llm_configured": llm_status["available"],
        "llm_model": llm_status.get("model"),
        "llm_provider": llm_status["provider"],
        "offline_mode": True
    }


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file with active high-accuracy model."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    result = recognizer.transcribe_audio_bytes(audio_bytes)
    return result


@app.post("/api/train-voice")
async def train_voice(
    speaker_name: str = Form(...),
    samples: List[UploadFile] = File(...)
):
    """
    Train and enroll a new voice profile from 3+ audio samples.
    Computes MFCC embeddings and acoustic baseline.
    """
    if not samples:
        raise HTTPException(status_code=400, detail="No audio samples uploaded")

    audio_bytes_list = []
    for sample in samples:
        data = await sample.read()
        if data:
            audio_bytes_list.append(data)

    result = voice_trainer.train_profile(speaker_name, audio_bytes_list)
    return result


@app.get("/api/voice-profiles")
async def list_voice_profiles():
    """List all enrolled speaker profiles."""
    profiles = voice_trainer.list_profiles()
    return {"profiles": profiles, "active": voice_trainer.active_profile}


@app.post("/api/verify-voice")
async def verify_voice(audio: UploadFile = File(...)):
    """Verify speaker against the enrolled profile."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    result = voice_trainer.verify_voice(audio_bytes)
    return result


@app.post("/api/analyze-web")
async def analyze_web_query(req: QueryRequest):
    """Deep web research, scraping, and AI/NLP synthesis."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = web_analyzer.analyze_web(req.query.strip())
    return result


@app.get("/api/llm/status")
async def llm_status():
    """Get local LLM status and configuration."""
    return llm_provider.get_status()


@app.post("/api/calibrate-noise")
async def calibrate_noise():
    """Measure room ambient noise floor."""
    val = recognizer.calibrate_noise(duration=1.0)
    return {"energy_threshold": val or 400}


@app.post("/api/settings")
async def update_settings(settings: SettingsRequest):
    """Update recognizer settings and model weights."""
    recognizer.set_engine(settings.engine, settings.whisper_model)
    if recognizer.sr_recognizer and settings.energy_threshold:
        recognizer.sr_recognizer.energy_threshold = settings.energy_threshold

    return {
        "success": True,
        "engine": recognizer.engine_type,
        "model": recognizer.model_size,
        "energy_threshold": settings.energy_threshold
    }

@app.post("/api/llm/configure")
async def configure_llm(req: QueryRequest):
    """Configure local LLM provider and model."""
    global llm_provider
    llm_provider = LLMProvider(
        provider=req.query or os.getenv("LLM_PROVIDER", "ollama"),
        model_name=req.query or os.getenv("LLM_MODEL", "neural-chat"),
        endpoint=os.getenv("LLM_ENDPOINT", "http://localhost:11434"),
        timeout=int(os.getenv("LLM_TIMEOUT", "30"))
    )
    return {"success": True, "provider": llm_provider.provider, "model": llm_provider.model_name, "available": llm_provider.is_available}


@app.post("/api/speak")
async def speak_text(req: SpeakRequest):
    """Queue speech synthesis."""
    tts.speak(req.text)
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
