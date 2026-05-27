"""
ollama_adapter.py — Adapter for locally running models via Ollama.

Ollama lets you run open-source models (Llama 3, Mistral, etc.) on your own machine
with zero API costs. Great for development and testing.

Requirements:
    - Install Ollama: https://ollama.ai
    - Pull a model: `ollama pull llama3`
    - No Python packages needed (uses the built-in `requests` library)

Usage:
    from scanner.adapters.ollama_adapter import OllamaAdapter
    adapter = OllamaAdapter(model="llama3")
"""

import json
import requests
from .base import BaseLLMAdapter, LLMResponse


class OllamaAdapter(BaseLLMAdapter):
    """Sends prompts to a locally running Ollama instance."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        Args:
            model:    The Ollama model name. Run `ollama list` to see installed models.
            base_url: URL where Ollama is running. Default is localhost:11434.
        """
        self.model = model
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return f"ollama/{self.model}"

    def send(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Send a prompt to Ollama's local API and return the response."""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                "stream": False,    # Get the full response at once instead of streaming
                "options": {
                    "temperature": 0,   # Deterministic output for consistent scanning
                }
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60,     # Local models can be slow, give them time
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            return LLMResponse(content=content, model=self.model, provider="ollama")

        except requests.ConnectionError:
            return LLMResponse(
                content="", model=self.model, provider="ollama",
                error="Could not connect to Ollama. Is it running? Try: ollama serve"
            )
        except Exception as e:
            return LLMResponse(content="", model=self.model, provider="ollama", error=str(e))
