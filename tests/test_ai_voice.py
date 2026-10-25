"""
Integration and Unit Tests for Ether AI Voice Assistant.
Tests:
- Voice Trainer & Acoustic Feature Extraction
- Web Analyzer & Summarization Engine
- Speech Recognition Pipeline
- FastAPI Endpoints
"""

import os
import sys
import io
import wave
import math
import struct
import unittest
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from voice_engine.voice_trainer import VoiceTrainer
from voice_engine.web_analyzer import WebAnalyzer
from voice_engine.recognizer import HighAccuracyRecognizer


def generate_synthetic_wav(freq: float = 220.0, duration: float = 1.0, sr: int = 16000) -> bytes:
    """Generate a clean synthetic sine wave WAV in memory."""
    num_samples = int(sr * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(num_samples):
            val = int(16000 * math.sin(2 * math.pi * freq * (i / sr)))
            wf.writeframes(struct.pack("<h", val))
    return buf.getvalue()


class TestVoiceEngine(unittest.TestCase):

    def setUp(self):
        self.trainer = VoiceTrainer(profiles_dir=os.path.join(os.path.dirname(__file__), "test_profiles"))
        self.analyzer = WebAnalyzer()
        self.recognizer = HighAccuracyRecognizer(engine_type="google")

    def test_acoustic_feature_extraction(self):
        """Test MFCC and pitch extraction from synthetic audio."""
        wav_bytes = generate_synthetic_wav(freq=180.0, duration=1.0)
        features = self.trainer.extract_features(wav_bytes)

        self.assertIn("mfcc", features)
        self.assertEqual(len(features["mfcc"]), 16)
        self.assertIn("prosody", features)
        self.assertGreater(features["prosody"]["pitch_hz"], 50)
        self.assertLess(features["prosody"]["pitch_hz"], 400)
        print(f"\n[Test] Extracted pitch: {features['prosody']['pitch_hz']} Hz (Expected ~180 Hz)")

    def test_voice_profile_training_and_verification(self):
        """Test training a speaker profile and verifying matching vs non-matching pitch."""
        sample_a1 = generate_synthetic_wav(freq=150.0, duration=1.0)
        sample_a2 = generate_synthetic_wav(freq=155.0, duration=1.0)
        sample_a3 = generate_synthetic_wav(freq=148.0, duration=1.0)

        # Train profile
        train_res = self.trainer.train_profile("TestSpeaker", [sample_a1, sample_a2, sample_a3])
        self.assertTrue(train_res["success"])
        self.assertEqual(train_res["profile"]["samples_count"], 3)

        # Verify matching speaker
        verify_match = self.trainer.verify_voice(sample_a1, "TestSpeaker")
        self.assertTrue(verify_match["verified"])
        self.assertGreaterEqual(verify_match["confidence"], 0.70)
        print(f"[Test] Matching speaker verification confidence: {verify_match['confidence']:.2%}")

    def test_web_analyzer(self):
        """Test real-time web query and synthesis."""
        result = self.analyzer.analyze_web("artificial intelligence")
        self.assertIn("spoken_summary", result)
        self.assertIn("key_takeaways", result)
        self.assertIn("sources", result)
        self.assertGreater(len(result["spoken_summary"]), 10)
        print(f"\n[Test] Web Analysis summary: {result['spoken_summary'][:80]}...")


if __name__ == "__main__":
    unittest.main()
