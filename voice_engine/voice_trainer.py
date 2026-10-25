import os
import json
import wave
import io
import math
import logging
from typing import Dict, Any, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceTrainer")

try:
    import numpy as np
except ImportError:
    np = None

try:
    from scipy.fftpack import dct
    from scipy.signal import find_peaks
except ImportError:
    dct = None
    find_peaks = None


class VoiceTrainer:
    """
    Voice Profile Training & Speaker Verification Engine.
    Enrolls user voice samples, extracts acoustic features (MFCC, pitch, spectral centroid),
    and computes acoustic similarity for speaker verification.
    """

    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir is None:
            self.profiles_dir = os.path.join(os.path.dirname(__file__), "..", "voice_profiles")
        else:
            self.profiles_dir = profiles_dir

        self.profiles_dir = os.path.abspath(self.profiles_dir)
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.active_profile = None
        self.active_profile = self.get_default_profile()

    def _extract_pcm_from_wav_bytes(self, wav_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Convert WAV bytes to float32 numpy array and return sample rate."""
        if np is None:
            raise RuntimeError("NumPy is required for voice feature extraction")

        with io.BytesIO(wav_bytes) as bio:
            with wave.open(bio, "rb") as wf:
                sr = wf.getframerate()
                n_channels = wf.getnchannels()
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

                audio_data = np.frombuffer(frames, dtype=dtype)
                if n_channels > 1:
                    audio_data = audio_data[::n_channels]

                # Normalize to float32 in [-1.0, 1.0]
                audio_float = audio_data.astype(np.float32) / (np.iinfo(dtype).max if dtype != np.uint8 else 128.0)
                return audio_float, sr

    def _compute_mfcc_simple(self, signal: np.ndarray, sr: int, num_ceps: int = 13) -> np.ndarray:
        """
        Pure NumPy / SciPy computation of Mel-Frequency Cepstral Coefficients (MFCCs).
        Robust and dependency-light without needing full librosa.
        """
        if len(signal) == 0:
            return np.zeros(num_ceps, dtype=np.float32)

        # Pre-emphasis filter
        pre_emphasis = 0.97
        emphasized = np.append(signal[0], signal[1:] - pre_emphasis * signal[:-1])

        # Framing
        frame_size = int(0.025 * sr)
        frame_stride = int(0.010 * sr)
        frame_length = len(emphasized)
        
        if frame_length < frame_size:
            emphasized = np.pad(emphasized, (0, frame_size - frame_length), mode="constant")
            frame_length = len(emphasized)

        num_frames = 1 + int(math.floor((frame_length - frame_size) / frame_stride))
        indices = np.tile(np.arange(0, frame_size), (num_frames, 1)) + np.tile(
            np.arange(0, num_frames * frame_stride, frame_stride), (frame_size, 1)
        ).T
        frames = emphasized[indices.astype(np.int32, copy=False)]

        # Windowing (Hamming)
        frames *= np.hamming(frame_size)

        # FFT & Power spectrum
        nfft = 512
        mag_frames = np.absolute(np.fft.rfft(frames, nfft))
        pow_frames = (1.0 / nfft) * (mag_frames ** 2)

        # Mel Filterbank
        nfilt = 26
        low_freq_mel = 0
        high_freq_mel = 2595 * np.log10(1 + (sr / 2) / 700)
        mel_points = np.linspace(low_freq_mel, high_freq_mel, nfilt + 2)
        hz_points = 700 * (10 ** (mel_points / 2595) - 1)
        bin_points = np.floor((nfft + 1) * hz_points / sr).astype(np.int32)

        fbank = np.zeros((nfilt, int(np.floor(nfft / 2 + 1))))
        for m in range(1, nfilt + 1):
            f_m_minus = bin_points[m - 1]
            f_m = bin_points[m]
            f_m_plus = bin_points[m + 1]

            for k in range(f_m_minus, f_m):
                fbank[m - 1, k] = (k - bin_points[m - 1]) / max(1, (bin_points[m] - bin_points[m - 1]))
            for k in range(f_m, f_m_plus):
                fbank[m - 1, k] = (bin_points[m + 1] - k) / max(1, (bin_points[m + 1] - bin_points[m]))

        filter_banks = np.dot(pow_frames, fbank.T)
        filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)
        filter_banks = 20 * np.log10(filter_banks)

        # Discrete Cosine Transform (DCT)
        if dct is not None:
            mfcc = dct(filter_banks, type=2, axis=1, norm="ortho")[:, :num_ceps]
        else:
            # Fallback direct DCT formula
            N = filter_banks.shape[1]
            k = np.arange(num_ceps)[:, None]
            n = np.arange(N)[None, :]
            dct_matrix = np.cos(np.pi * k * (2 * n + 1) / (2 * N))
            mfcc = np.dot(filter_banks, dct_matrix.T)

        # Average across all frames to get single 1D feature vector
        mean_mfcc = np.mean(mfcc, axis=0)
        return mean_mfcc

    def _estimate_pitch_and_timbre(self, signal: np.ndarray, sr: int) -> Dict[str, float]:
        """Estimate mean fundamental pitch (F0), zero-crossing rate, and spectral centroid."""
        if len(signal) == 0:
            return {"pitch_hz": 120.0, "spectral_centroid": 1500.0, "zcr": 0.05, "energy": 0.1}

        # Zero crossing rate
        zcr = float(np.mean(np.abs(np.diff(np.sign(signal))) > 0))

        # Root mean square energy
        energy = float(np.sqrt(np.mean(signal ** 2)))

        # Spectral Centroid
        spectrum = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(len(signal), d=1.0 / sr)
        spectral_sum = np.sum(spectrum)
        if spectral_sum > 0:
            spectral_centroid = float(np.sum(freqs * spectrum) / spectral_sum)
        else:
            spectral_centroid = 1500.0

        # Pitch estimation using normalized autocorrelation
        pitch_hz = 120.0
        corr = np.correlate(signal, signal, mode="full")
        corr = corr[len(corr) // 2:]

        # Search range: 60Hz to 400Hz (human voice range)
        min_lag = int(sr / 400)
        max_lag = int(sr / 60)

        if max_lag < len(corr) and min_lag < max_lag:
            peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
            if peak_lag > 0 and corr[peak_lag] > 0.1 * corr[0]:
                pitch_hz = float(sr / peak_lag)

        return {
            "pitch_hz": round(pitch_hz, 1),
            "spectral_centroid": round(spectral_centroid, 1),
            "zcr": round(zcr, 4),
            "energy": round(energy, 4)
        }

    def extract_features(self, wav_bytes: bytes) -> Dict[str, Any]:
        """Extract complete acoustic feature set from audio bytes."""
        signal, sr = self._extract_pcm_from_wav_bytes(wav_bytes)
        mfcc = self._compute_mfcc_simple(signal, sr, num_ceps=16)
        prosody = self._estimate_pitch_and_timbre(signal, sr)

        return {
            "mfcc": mfcc.tolist(),
            "prosody": prosody,
            "duration_sec": round(len(signal) / sr, 2),
            "sample_rate": sr
        }

    def train_profile(
        self,
        profile_name: str,
        audio_samples: List[bytes],
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Train a new speaker profile from multiple audio samples.
        Aggregates MFCC embeddings and acoustic parameters.
        """
        if not audio_samples:
            return {"success": False, "error": "No audio samples provided"}

        logger.info(f"Training voice profile '{profile_name}' with {len(audio_samples)} samples...")
        all_mfccs = []
        all_pitches = []
        all_centroids = []
        all_energies = []

        for i, sample in enumerate(audio_samples):
            try:
                feat = self.extract_features(sample)
                all_mfccs.append(feat["mfcc"])
                all_pitches.append(feat["prosody"]["pitch_hz"])
                all_centroids.append(feat["prosody"]["spectral_centroid"])
                all_energies.append(feat["prosody"]["energy"])
            except Exception as e:
                logger.error(f"Error processing sample {i}: {e}")

        if not all_mfccs:
            return {"success": False, "error": "Failed to extract features from any samples"}

        mfcc_arr = np.array(all_mfccs)
        centroid_mfcc = np.mean(mfcc_arr, axis=0)
        std_mfcc = np.std(mfcc_arr, axis=0)

        # Profile definition
        profile_data = {
            "profile_name": profile_name,
            "samples_count": len(all_mfccs),
            "created_at": json.dumps(os.path.getmtime(self.profiles_dir)),
            "mean_pitch_hz": round(float(np.mean(all_pitches)), 1),
            "mean_spectral_centroid": round(float(np.mean(all_centroids)), 1),
            "mean_energy": round(float(np.mean(all_energies)), 4),
            "verification_threshold": 0.75,
            "status": "trained",
            "centroid_vector": centroid_mfcc.tolist(),
            "std_vector": std_mfcc.tolist()
        }

        # Save profile metadata JSON
        profile_path = os.path.join(self.profiles_dir, f"{profile_name.lower().replace(' ', '_')}.json")
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        self.active_profile = profile_name
        logger.info(f"Successfully trained and saved profile to {profile_path}")

        return {
            "success": True,
            "profile": profile_data,
            "message": f"Voice profile '{profile_name}' trained successfully with {len(all_mfccs)} samples."
        }

    def verify_voice(self, wav_bytes: bytes, target_profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify if an audio sample matches the enrolled speaker profile.
        Uses Cosine Similarity between MFCC feature vectors.
        """
        target = target_profile_name or self.active_profile
        if not target:
            return {
                "verified": True,
                "confidence": 1.0,
                "note": "No profile trained yet; running in open speaker mode"
            }

        target_file = os.path.join(self.profiles_dir, f"{target.lower().replace(' ', '_')}.json")
        if not os.path.exists(target_file):
            return {
                "verified": True,
                "confidence": 1.0,
                "note": f"Profile '{target}' not found; running in default mode"
            }

        with open(target_file, "r", encoding="utf-8") as f:
            profile = json.load(f)

        try:
            feat = self.extract_features(wav_bytes)
            sample_mfcc = np.array(feat["mfcc"])
            target_mfcc = np.array(profile["centroid_vector"])

            # Cosine similarity
            dot = np.dot(sample_mfcc, target_mfcc)
            norm_a = np.linalg.norm(sample_mfcc)
            norm_b = np.linalg.norm(target_mfcc)

            if norm_a == 0 or norm_b == 0:
                sim = 0.5
            else:
                sim = float(dot / (norm_a * norm_b))
                # Normalize cosine range [-1, 1] to [0, 1]
                sim = (sim + 1.0) / 2.0

            threshold = profile.get("verification_threshold", 0.75)
            is_match = sim >= threshold

            return {
                "verified": is_match,
                "confidence": round(sim, 3),
                "threshold": threshold,
                "profile_name": profile["profile_name"],
                "sample_pitch_hz": feat["prosody"]["pitch_hz"],
                "expected_pitch_hz": profile.get("mean_pitch_hz", 120.0)
            }
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return {"verified": True, "confidence": 0.8, "error": str(e)}

    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all enrolled voice profiles."""
        profiles = []
        if not os.path.exists(self.profiles_dir):
            return profiles

        for fname in os.listdir(self.profiles_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.profiles_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profiles.append({
                            "name": data.get("profile_name", fname[:-5]),
                            "samples": data.get("samples_count", 0),
                            "pitch_hz": data.get("mean_pitch_hz"),
                            "status": data.get("status", "ready"),
                            "is_active": data.get("profile_name") == self.active_profile
                        })
                except Exception:
                    pass
        return profiles

    def get_default_profile(self) -> Optional[str]:
        """Get the first or active profile."""
        profiles = self.list_profiles()
        if profiles:
            return profiles[0]["name"]
        return None
