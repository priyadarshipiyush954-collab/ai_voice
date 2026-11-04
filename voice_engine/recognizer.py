import os
import io
import time
import wave
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VoiceRecognizer")

try:
    import numpy as np
except ImportError:
    np = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

# Faster-whisper for state-of-the-art offline transcription
try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


class HighAccuracyRecognizer:
    """
    Local-Only Speech Recognition System using Faster-Whisper.
    All transcription is performed on-device with no cloud API calls.
    """

    def __init__(
        self,
        engine_type: str = "whisper",
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
        energy_threshold: int = 400,
        dynamic_energy_threshold: bool = True
    ):
        self.engine_type = engine_type
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.whisper_model = None
        self.sr_recognizer = None

        # Assistant vocabulary bias prompt for Whisper
        self.initial_prompt = (
            "Ether, analyze, explain, what is, who is, tell me about, "
            "search, volume, stop, resume, question, answer."
        )

        # Initialize SpeechRecognition for microphone capture only
        if sr:
            self.sr_recognizer = sr.Recognizer()
            self.sr_recognizer.energy_threshold = energy_threshold
            self.sr_recognizer.dynamic_energy_threshold = dynamic_energy_threshold
            self.sr_recognizer.dynamic_energy_adjustment_damping = 0.15
            self.sr_recognizer.dynamic_energy_ratio = 1.5
            self.sr_recognizer.pause_threshold = 0.8
            self.sr_recognizer.non_speaking_duration = 0.5

        # Load Whisper model
        if HAS_FASTER_WHISPER:
            self._load_whisper_model()
        else:
            logger.error("Faster-Whisper is required for offline speech recognition. Install with: pip install faster-whisper")

    def _load_whisper_model(self):
        """Load local Whisper model for offline transcription."""
        if self.whisper_model is None and HAS_FASTER_WHISPER:
            try:
                logger.info(f"Loading Whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
                model_path = os.getenv(
                    "WHISPER_MODEL_PATH",
                    os.path.join(os.path.dirname(__file__), "..", ".cache", "whisper")
                )
                self.whisper_model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=model_path
                )
                logger.info(f"Whisper model loaded successfully from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                logger.error("Ensure model is downloaded or WHISPER_MODEL_PATH is set correctly")
                logger.error("Models can be pre-downloaded with: python -c \"from faster_whisper import WhisperModel; WhisperModel('base.en')\"")

    def set_engine(self, engine_type: str, model_size: Optional[str] = None):
        """Switch Whisper model dynamically."""
        self.engine_type = engine_type
        if model_size and model_size != self.model_size:
            self.model_size = model_size
            self.whisper_model = None
            self._load_whisper_model()

    def calibrate_noise(self, duration: float = 1.0):
        """Calibrate microphone for ambient noise floor."""
        if not sr or not self.sr_recognizer:
            return None
        try:
            with sr.Microphone() as source:
                logger.info(f"Calibrating ambient noise floor for {duration}s...")
                self.sr_recognizer.adjust_for_ambient_noise(source, duration=duration)
                logger.info(f"Calibrated energy threshold: {self.sr_recognizer.energy_threshold:.1f}")
                return self.sr_recognizer.energy_threshold
        except Exception as e:
            logger.error(f"Failed to calibrate noise: {e}")
            return None

    def listen_from_mic(self, timeout: int = 5, phrase_time_limit: int = 7) -> Dict[str, Any]:
        """
        Listen to microphone and transcribe with highest accuracy.
        Returns dict with text, confidence, and engine used.
        """
        if not sr:
            return {"success": False, "error": "SpeechRecognition not installed"}

        try:
            with sr.Microphone() as source:
                # Dynamic noise adjustment before listening
                self.sr_recognizer.adjust_for_ambient_noise(source, duration=0.6)
                logger.info("Listening for command...")
                audio = self.sr_recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

                # Process raw audio bytes
                raw_wav = audio.get_wav_data(convert_rate=16000, convert_width=2)
                return self.transcribe_audio_bytes(raw_wav)

        except sr.WaitTimeoutError:
            return {"success": False, "error": "No speech detected (timeout)", "text": ""}
        except Exception as e:
            logger.error(f"Error during microphone listening: {e}")
            return {"success": False, "error": str(e), "text": ""}

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribe audio bytes (WAV/PCM) using local Whisper model.
        No cloud API calls are made.
        """
        start_time = time.time()

        if self.whisper_model is None:
            return {
                "success": False,
                "error": "Whisper model not loaded. Ensure faster-whisper is installed and model is available.",
                "text": "",
                "latency_ms": 0
            }

        try:
            result = self._transcribe_with_whisper(audio_bytes)
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "latency_ms": int((time.time() - start_time) * 1000)
            }

    def _wav_bytes_to_float32(self, audio_bytes: bytes) -> Optional[np.ndarray]:
        """Convert standard WAV bytes to float32 NumPy array at 16kHz without disk I/O."""
        if np is None:
            return None
        try:
            with io.BytesIO(audio_bytes) as bio:
                with wave.open(bio, "rb") as wf:
                    sr = wf.getframerate()
                    n_ch = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    frames = wf.readframes(wf.getnframes())

                    if sampwidth == 2:
                        dtype = np.int16
                    elif sampwidth == 1:
                        dtype = np.uint8
                    elif sampwidth == 4:
                        dtype = np.int32
                    else:
                        dtype = np.int16

                    audio = np.frombuffer(frames, dtype=dtype)
                    if n_ch > 1:
                        audio = audio[::n_ch]

                    audio_float = audio.astype(np.float32) / (np.iinfo(dtype).max if dtype != np.uint8 else 128.0)

                    # Resample to 16000 Hz if necessary
                    if sr != 16000 and len(audio_float) > 0:
                        try:
                            import scipy.signal
                            num_target = int(len(audio_float) * 16000 / sr)
                            audio_float = scipy.signal.resample(audio_float, num_target).astype(np.float32)
                        except Exception as e:
                            logger.debug(f"Resampling error: {e}")

                    return audio_float
        except Exception:
            return None

    def _transcribe_with_whisper(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Transcribe using Faster-Whisper with in-memory array or temp file fallback."""
        audio_input = self._wav_bytes_to_float32(audio_bytes)
        tmp_path = None

        if audio_input is None:
            # Fallback to temp file if not PCM WAV (e.g., WebM)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(audio_bytes)
            audio_input = tmp_path

        try:
            segments, info = self.whisper_model.transcribe(
                audio_input,
                beam_size=5,
                initial_prompt=self.initial_prompt,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                language="en"
            )

            text_segments = []
            confidences = []
            for seg in segments:
                text_segments.append(seg.text.strip())
                prob = max(0.0, min(1.0, float(np.exp(seg.avg_logprob)) if np else 0.9))
                confidences.append(prob)

            full_text = " ".join(text_segments).strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.95

            return {
                "success": True,
                "text": full_text,
                "confidence": round(avg_conf, 2),
                "engine": "faster-whisper",
                "model": self.model_size,
                "language": getattr(info, "language", "en"),
                "offline_mode": True
            }
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
