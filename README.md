# Ether AI Voice Assistant 🎙⚡

An advanced, high-accuracy AI Voice Assistant with **Speaker Profile Training**, **Deep Web Analysis & AI Summarization**, **Spotify Media Control**, and a **Modern Light-Theme Web UI** designed following the **UI/UX Pro Max** Swiss & Minimalist design intelligence guidelines.

---

## 🌟 What's New in v2.0 Pro

1. **High-Accuracy Speech Recognition Engine**:
   - Integrated **OpenAI Faster-Whisper** transformer models (`tiny.en`, `base.en`, `small.en`) with custom assistant & music vocabulary prompt biasing.
   - Dual-engine architecture with **Cloud Adaptive Google Speech Recognition** fallback.
   - Dynamic ambient noise floor calibration (adaptive energy thresholding, room noise filtering).

2. **Train With Voices (Speaker Verification & Enrollment)**:
   - Interactive 3-step voice enrollment studio (Wake word, conversational speech, commands).
   - Acoustic feature extraction: Mel-Frequency Cepstral Coefficients (MFCCs), fundamental pitch ($F_0$), spectral centroid, and timbre.
   - Cosine similarity speaker verification to prevent unauthorized activations and customize acoustic sensitivity per user.

3. **Deep Web Analysis**:
   - Multi-source search (DuckDuckGo, Wikipedia, Live web scraping).
   - Text summarization with spoken-friendly executive summaries and key bullet-point takeaways.
   - Verified source citations and external URLs.
   - Optional Gemini AI multimodal synthesis integration (`GEMINI_API_KEY`).

4. **Modern Light-Theme Web Application**:
   - Designed using **UI/UX Pro Max** principles (Light Swiss / Modern Clean Minimalist).
   - Plus Jakarta Sans typography, high-contrast Slate 900 text, crisp white card surfaces, soft borders, and responsive layout.
   - **Real-time Web Audio API waveform & frequency spectrum visualizer**.
   - One-click quick action chips, live confidence indicators, and TTS voice playback.

5. **Spotify Media Controller**:
   - Hands-free track search, smart device auto-transfer, and playback controls (play, pause, next, previous).
   - Live album art, track metadata, and real-time progress bar.

---

## 🚀 Quick Start

### 1. Activate Virtual Environment
```bash
# In PowerShell:
& "D:\d drive\ai_voice\.venv\Scripts\Activate.ps1"
```

### 2. Launch the Web Interface (Recommended)
```bash
python ai_voice.py --web
```
Or directly with uvicorn:
```bash
python -m uvicorn app:app --reload --port 8000
```
Open your browser at **[http://localhost:8000](http://localhost:8000)** to access the light-theme UI.

### 3. Launch in Terminal Voice-Only Mode
```bash
python ai_voice.py --cli
```
Say `"Ether"` to wake up the assistant, followed by your command!

---

## 🎙 Voice Commands Guide

| Voice Command | Action |
|---|---|
| `"Ether, play Bohemian Rhapsody"` | Searches Spotify for Bohemian Rhapsody and starts playback on active device |
| `"Ether, analyze the web for latest breakthroughs in AI"` | Performs deep web research, scrapes articles, and speaks an executive summary |
| `"Ether, what is quantum computing?"` | Explains quantum computing with key bullet points and sources |
| `"Ether, who is the CEO of Google?"` | Instant web answer lookup |
| `"Ether, pause music"` / `"Ether, next song"` | Controls Spotify playback |
| `"Ether, stop listening"` | Puts assistant to sleep / exits daemon |

---

## ⚙ Configuration (`.env`)

Copy `.env.example` to `.env` to configure optional integrations:
```env
# Spotify Integration (Optional)
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback

# Gemini AI Synthesis (Optional - for advanced web reasoning)
GEMINI_API_KEY=your_gemini_key

# Engine Defaults
DEFAULT_ENGINE=whisper
DEFAULT_WHISPER_MODEL=base.en
ENERGY_THRESHOLD=400
```

---

## 📁 Project Architecture

```
ai_voice/
├── ai_voice.py              # Core voice daemon and CLI launcher
├── app.py                   # FastAPI REST API & WebSocket backend
├── voice_engine/            # Modular Voice & AI Engine
│   ├── recognizer.py        # High-accuracy Whisper & Google SR engine
│   ├── voice_trainer.py     # MFCC feature extraction & speaker profile training
│   ├── web_analyzer.py      # Real-time web scraper, search & AI summarizer
│   ├── spotify_controller.py# Spotify media and device controller
│   └── tts.py               # Thread-safe Text-to-Speech queue
├── voice_profiles/          # Saved speaker embeddings and JSON profiles
├── web/                     # Modern Light-Theme Frontend (UI/UX Pro Max)
│   ├── index.html           # Accessible semantic layout
│   ├── styles.css           # Clean Swiss light theme & Plus Jakarta Sans
│   └── app.js               # AudioContext visualizer & interactive controller
├── design-system/           # UI/UX Pro Max persisted design tokens
└── .env.example             # Configuration template
```
