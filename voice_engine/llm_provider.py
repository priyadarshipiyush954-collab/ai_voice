"""
Local Language Model Provider for Offline Inference
Supports Ollama and Llama.cpp runtimes with pluggable model configurations.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger("LLMProvider")


class LLMProvider:
    """
    Local LLM interface supporting Ollama, Llama.cpp, and other local runtimes.
    All inference is performed on-device; no cloud APIs are called.
    """

    def __init__(
        self,
        provider: str = "ollama",  # "ollama", "llama_cpp", "none"
        model_name: str = "neural-chat",
        endpoint: str = "http://localhost:11434",
        timeout: int = 30
    ):
        """
        Initialize local LLM provider.

        Args:
            provider: Runtime type ('ollama', 'llama_cpp', or 'none' for disabled)
            model_name: Model name (e.g., 'neural-chat', 'mistral', 'llama2')
            endpoint: Local endpoint URL
            timeout: Request timeout in seconds
        """
        self.provider = provider
        self.model_name = model_name
        self.endpoint = endpoint
        self.timeout = timeout
        self.is_available = False
        self.last_error = None

        if provider == "none":
            logger.info("LLM provider disabled (offline mode without AI synthesis)")
            return

        # Verify the local runtime is accessible
        self._verify_provider()

    def _verify_provider(self):
        """Check if the local LLM runtime is running and model is available."""
        if self.provider == "ollama":
            self._verify_ollama()
        elif self.provider == "llama_cpp":
            self._verify_llama_cpp()

    def _verify_ollama(self):
        """Verify Ollama runtime and model availability."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.endpoint}/api/tags", timeout=2)
            if response.status_code != 200:
                self.last_error = "Ollama not responding"
                logger.warning(f"Ollama verification failed: {self.last_error}")
                return

            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            if self.model_name not in models:
                self.last_error = f"Model '{self.model_name}' not found in Ollama"
                logger.warning(f"{self.last_error}. Available models: {models}")
                logger.info(f"To download: ollama pull {self.model_name}")
                return

            self.is_available = True
            logger.info(f"Ollama ready with model: {self.model_name}")
        except requests.exceptions.ConnectionError:
            self.last_error = f"Cannot connect to Ollama at {self.endpoint}"
            logger.warning(self.last_error)
        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"Ollama verification error: {e}")

    def _verify_llama_cpp(self):
        """Verify Llama.cpp runtime availability."""
        try:
            # Llama.cpp typically runs on localhost:8000
            response = requests.get(f"{self.endpoint}/health", timeout=2)
            if response.status_code == 200:
                self.is_available = True
                logger.info(f"Llama.cpp ready")
                return

            self.last_error = "Llama.cpp server not responding"
            logger.warning(self.last_error)
        except requests.exceptions.ConnectionError:
            self.last_error = f"Cannot connect to Llama.cpp at {self.endpoint}"
            logger.warning(self.last_error)
        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"Llama.cpp verification error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Return LLM provider status and configuration."""
        return {
            "provider": self.provider,
            "available": self.is_available,
            "model": self.model_name if self.is_available else None,
            "endpoint": self.endpoint,
            "error": self.last_error if not self.is_available else None
        }

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using local LLM.
        Returns None if provider is unavailable.
        """
        if not self.is_available or self.provider == "none":
            return None

        try:
            if self.provider == "ollama":
                return self._generate_ollama(prompt, max_tokens, temperature)
            elif self.provider == "llama_cpp":
                return self._generate_llama_cpp(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None

        return None

    def _generate_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Generate using Ollama API."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "num_predict": max_tokens
            }

            response = requests.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "").strip()
                return text if text else None
            else:
                logger.warning(f"Ollama error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return None

    def _generate_llama_cpp(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Generate using Llama.cpp API."""
        try:
            payload = {
                "prompt": prompt,
                "temperature": temperature,
                "n_predict": max_tokens,
                "top_p": 0.9
            }

            response = requests.post(
                f"{self.endpoint}/completion",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get("content", "").strip()
                return text if text else None
            else:
                logger.warning(f"Llama.cpp error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Llama.cpp generation failed: {e}")
            return None

    def answer_question(self, question: str) -> Optional[str]:
        """
        Answer a question using the local LLM.
        Returns a concise, spoken-friendly response or None if unavailable.
        """
        if not self.is_available:
            return None

        prompt = (
            f"You are a helpful voice assistant. Answer the following question concisely "
            f"in 1-2 sentences suitable for text-to-speech playback.\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        response = self.generate(prompt, max_tokens=150, temperature=0.5)
        if response:
            # Clean up response
            response = response.strip()
            if response.endswith("\n"):
                response = response.rsplit("\n", 1)[0].strip()
        return response
