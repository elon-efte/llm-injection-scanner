"""
base.py — Abstract base class for all LLM adapters.

Every LLM backend (OpenAI, Anthropic, Ollama, etc.) must inherit from
BaseLLMAdapter and implement the `send()` method.
This lets the scanner swap backends without changing any other code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    """Holds the result of a single LLM call."""
    content: str                   # The text the model returned
    model: str                     # Model name used (e.g. "gpt-4")
    provider: str                  # Adapter name (e.g. "openai")
    error: Optional[str] = None    # If the call failed, the error message goes here


class BaseLLMAdapter(ABC):
    """
    Abstract base class all adapters must inherit from.

    To add a new LLM backend:
      1. Create a new file in scanner/adapters/
      2. Subclass BaseLLMAdapter
      3. Implement send() and name
    """

    @abstractmethod
    def send(self, system_prompt: str, user_message: str) -> LLMResponse:
        """
        Send a prompt to the LLM and return its response.

        Args:
            system_prompt: The system/context instructions given to the model.
            user_message:  The user message (this is where injections are injected).

        Returns:
            LLMResponse with the model's reply, or an error field if the call failed.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name, used in reports."""
        pass
