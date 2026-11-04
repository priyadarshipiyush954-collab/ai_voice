import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("OfflineAnalyzer")


class WebAnalyzer:
    """
    Offline Question Answering Engine using Local LLM.
    No web scraping, no remote API calls - purely local inference.
    """

    def __init__(self, llm_provider=None):
        """
        Initialize offline analyzer with a local LLM provider.

        Args:
            llm_provider: Instance of LLMProvider for local inference
        """
        self.llm = llm_provider

    def analyze_web(self, query: str) -> Dict[str, Any]:
        """
        Answer questions using local LLM without web access.
        Note: This is an offline-only implementation. Web search and scraping
        are not available. The LLM can only answer from its training data.
        """
        logger.info(f"Processing query offline: '{query}'")

        if not self.llm or not self.llm.is_available:
            return {
                "query": query,
                "spoken_summary": "I'm running in offline mode. Please configure a local language model to enable question answering.",
                "key_takeaways": [
                    "Local LLM is not configured or unavailable",
                    "Install Ollama and download a model to enable offline Q&A",
                    "Web search and current information lookups require internet access"
                ],
                "sources": [],
                "synthesis_method": "offline-unavailable",
                "offline_mode": True
            }

        # Use local LLM to answer the question
        response = self.llm.answer_question(query)

        if not response:
            return {
                "query": query,
                "spoken_summary": "I couldn't generate a response. The local model may be unavailable.",
                "key_takeaways": ["Local LLM inference failed"],
                "sources": [],
                "synthesis_method": "offline-error",
                "offline_mode": True
            }

        return {
            "query": query,
            "spoken_summary": response,
            "key_takeaways": [
                "Response generated from local LLM",
                "Note: Information is limited to model's training data",
                "For current events, internet access is required"
            ],
            "sources": [],
            "synthesis_method": "local-llm",
            "offline_mode": True,
            "model": self.llm.model_name
        }
