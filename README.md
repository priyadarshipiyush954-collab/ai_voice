# Ether AI Voice Assistant — Offline-Capable Local Voice Assistant

An **offline-first** voice assistant that runs completely without cloud APIs, Spotify, or internet connectivity (after initial setup). All processing happens locally on your device.

![Ether AI Voice Offline](https://img.shields.io/badge/Offline%20Capable-Yes-blue.svg?style=for-the-badge)
![Version](https://img.shields.io/badge/version-2.0.0-orange.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge)

## 🚀 Quick Start

### 1. Activate Virtual Environment
```bash
# In PowerShell:
& "D:\d drive\ai_voice\.venv\Scripts\Activate.ps1"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Local LLM (Required for Question Answering)
Download and run [Ollama](https://ollama.ai) and pull a model:

```bash
# Start Ollama server (it runs locally)
ollama serve

# Pull a model suitable for voice interaction
ollama pull neural-chat
# or
ollama pull mistral
# or
ollama pull llama3.2
```

### 4. Launch the Assistant

**Web UI (Recommended):**
```bash
python ai_voice.py --web
```
Open your browser at **[http://localhost:8000](http://localhost:8000)** to access the offline-capable UI.

**CLI Mode:**
```bash
python ai_voice.py --cli
```
Say `"Ether"` to wake up the assistant, followed by your command!

---

## 🎙 Voice Commands Guide

| Voice Command | Action |
|---|---|
| `"Ether, what is quantum computing?"` | Ask local LLM to explain a topic |
| `"Ether, explain machine learning basics"` | Explain concepts using local AI |
| `"Ether, what are the benefits of renewable energy?"` | Get offline answers |
| `"Ether, tell me about renewable energy"` | Voice Q&A with local model |
| `"Ether, analyze the web for..."` | ⚠️ *Offline — no web search* |
| `"Ether, play ..."` | ⚠️ *Removed — Spotify removed* |
| `"Ether, pause"` | ⚠️ *Removed — Spotify removed* |
| `"Ether, stop listening"` | Puts assistant to sleep / exits daemon |
| `"Ether, train with my voice"` | Enroll your voice profile |
| `"Ether, who am I?"` | Verify against enrolled profile |

---

## 📦 What Changed: Removed Features

### Spotify — Completely Removed
- ❌ `voice_engine/spotify_controller.py` — Deleted
- ❌ Spotify API routes (`/api/spotify/*`) — Removed from `app.py`
- ❌ Spotify command handling — Removed from `ai_voice.py`
- ❌ `spotipy` dependency — Removed from `requirements.txt`
- ❌ Spotify config in `.env.example` — Removed

### Cloud Services Removed
- ❌ Google Speech Recognition fallback — Removed from `recognizer.py`
- ❌ Gemini AI synthesis — Removed from `web_analyzer.py`
- ❌ DuckDuckGo web search — Removed from `web_analyzer.py`
- ❌ Web page scraping — Removed from `web_analyzer.py`
- ❌ CDN fonts from web UI — Replaced with local font fallback
- ❌ Remote API calls (Gemini, DuckDuckGo) — Removed
- ❌ Telemetry — Removed

### Dependencies Removed
- `spotipy>=2.24.0`
- `google-generativeai` (implicitly removed)
- Removed unused cloud API integrations

---

## 🧠 Local Language Model (LLM) Configuration

The assistant uses a **local LLM** running via Ollama or Llama.cpp for question answering. No cloud APIs, no API keys required.

### Configuration

Copy `.env.example` to `.env` and set:

```env
# Local LLM Provider
LLM_PROVIDER=ollama          # or "llama_cpp", "none"
LLM_MODEL=neural-chat        # Any model pre-downloaded via Ollama
LLM_ENDPOINT=http://localhost:11434
LLM_TIMEOUT=30

# Speech Recognition
DEFAULT_WHISPER_MODEL=base.en
ENERGY_THRESHOLD=400
WAKE_SENSITIVITY=80
```

### Supported Providers

**Ollama** (recommended):
- Install from: https://ollama.ai
- Pull models: `ollama pull neural-chat`, `ollama pull mistral`, etc.
- Runs on `http://localhost:11434` by default

**Llama.cpp**:
- Server must be running locally
- Configure `LLM_PROVIDER=llama_cpp` and `LLM_ENDPOINT` accordingly

**Disabled** (`none`):
- LLM question answering disabled
- Assistant only performs voice commands and TTS

---

## 🎤 Voice Features (Local Only)

### Speech Recognition
- **Faster-Whisper** — Transformer-based local speech-to-text
- No cloud API calls (no Google, no AssemblyAI, etc.)
- Models: `tiny.en`, `base.en`, `small.en` (pre-downloaded in `.cache/whisper/`)
- Configure via `DEFAULT_WHISPER_MODEL` in `.env`

### Text-To-Speech
- **pyttsx3** — Offline, local TTS engine
- No cloud voice services required
- Uses system voices (Windows SAPI, macOS, or eSpeak)
- Configure rate/volume in `voice_engine/tts.py`

### Voice Enrollment & Verification
- **MFCC-based speaker profiles** — Local only
- No biometric data leaves your device
- Enroll via web UI or CLI: `python ai_voice.py --train`
- Verify voice: System compares new sample against enrolled profiles

---

## 📁 Project Architecture (Offline-Capable)

```
ai_voice/
├── ai_voice.py              # Core CLI & Voice Daemon (offline-capable)
├── app.py                   # FastAPI REST API & WebSocket backend (offline-capable)
├── voice_engine/            # Modular Voice & AI Engine
│   ├── recognizer.py        # Faster-Whisper only (no Google fallback)
│   ├── voice_trainer.py     # MFCC feature extraction & speaker verification
│   ├── tts.py               # Thread-safe local Text-to-Speech (pyttsx3)
│   └── llm_provider.py      # NEW: Local LLM interface (Ollama/Llama.cpp)
│   └── web_analyzer.py      # Offline Q&A using local LLM (no web scraping)
├── voice_profiles/          # Saved speaker embeddings and JSON profiles
├── web/                     # Modern Frontend (local assets only, no CDN)
│   ├── index.html           # Updated: offline mode, no Spotify, local fonts
│   ├── styles.css           # Updated: local design tokens
│   └── app.js               # Updated: offline-first interaction
├── .cache/whisper/          # Pre-downloaded Whisper models (optional)
├── .env                     # Configuration (create from .env.example)
└── .env.example             # Updated: LLM + offline settings
```

---

## 🛠 Offline Setup Checklist

### Before Going Offline:

1. ✅ **Install dependencies**: `pip install -r requirements.txt`
2. ✅ **Download Whisper model** (one-time):
   ```bash
   python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"
   ```
3. ✅ **Download Ollama and LLM model**:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama serve
   ollama pull neural-chat
   ```
4. ✅ **Verify LLM is accessible**:
   ```bash
   curl http://localhost:11434/api/tags
   # Should return list of available models
   ```
5. ✅ **Copy model cache if air-gapping**:
   - Copy `.cache/whisper/` directory to target machine
   - Or set `WHISPER_MODEL_PATH` in `.env`

### Air-Gapped Deployment:

1. Prepare a connected machine with all dependencies installed
2. Download models: `ollama pull neural-chat`
3. Run: `python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"` to pre-download
4. Copy entire project directory (including `.cache/`)
5. On air-gapped machine, verify: `ollama list` and Whisper model loads
6. Start: `python ai_voice.py --web`

---

## 🔧 Troubleshooting

### "Whisper model not found" error
- Ensure you ran the pre-download command or set `WHISPER_MODEL_PATH` in `.env`
- Models are cached in `.cache/whisper/` by default

### "Cannot connect to Ollama" error
- Ensure Ollama is running: `ollama serve`
- Check `LLM_ENDPOINT` in `.env` matches your setup
- Verify: `curl http://localhost:11434/api/tags`

### "Model generates error on startup"
- Make sure you pulled a valid model: `ollama list`
- Recommended: `neural-chat` or `mistral` for voice interactions

### Web UI shows "Loading..." or fails to connect
- Check console for CORS or static file errors
- Ensure `web/` directory is served correctly by FastAPI
- Verify `styles.css` exists in `web/` directory

### No response to questions
- Verify LLM provider is configured and available in `.env`
- Check `LLM_PROVIDER` and `LLM_MODEL` settings
- View status at `http://localhost:8000/api/llm/status`

### "Energy threshold too low/high" issues
- Adjust `ENERGY_THRESHOLD` in `.env` (typical range: 200-800)
- Use web UI calibration or CLI: `python ai_voice.py --calibrate`

---

## 📊 Current Limitations (Offline Mode)

| Feature | Status | Notes |
|---|---|---|
| **Speech Recognition** | ✅ Fully offline | Whisper models only |
| **Text-To-Speech** | ✅ Fully offline | pyttsx3 local engine |
| **Voice Enrollment** | ✅ Fully offline | Local MFCC features |
| **Voice Verification** | ✅ Fully offline | Cosine similarity comparison |
| **Question Answering** | ✅ Offline (with LLM) | Requires local LLM (Ollama) |
| **Web Search** | ❌ Not available | Offline-only mode |
| **Current Information** | ❌ Not available | Model's training data cutoff |
| **Spotify Control** | ❌ Removed | Feature deleted per requirements |
| **Google Speech Fallback** | ❌ Removed | Whisper only |
| **Gemini AI Synthesis** | ❌ Removed | Local LLM only |
| **Remote API Calls** | ❌ Removed | Fully offline-capable |
| **CDN Fonts/Assets** | ❌ Removed | Local fonts only |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ether AI Voice Assistant** — Your privacy-first, offline-capable local voice assistant. All audio processing and AI inference happens on your device. No data leaves your machine.