"""
openai_adapter.py — Adapter for OpenAI's GPT models (GPT-4, GPT-3.5-turbo, etc.)

Requirements:
    pip install openai

Usage:
    from scanner.adapters.openai_adapter import OpenAIAdapter
    adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4")
"""

from .base import BaseLLMAdapter, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    """Sends prompts to OpenAI's Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Args:
            api_key: Your OpenAI API key (starts with sk-...)
            model:   Which model to use. Default is gpt-3.5-turbo (cheaper for testing).
                     Use "gpt-4" or "gpt-4o" for stronger tests.
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    @property
    def name(self) -> str:
        return f"openai/{self.model}"

    def send(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Send a chat message to OpenAI and return the response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                temperature=0,      # Keep outputs deterministic for consistent scanning
                max_tokens=1024,
            )
            content = response.choices[0].message.content or ""
            return LLMResponse(content=content, model=self.model, provider="openai")

        except Exception as e:
            # Return an error response so the scanner can log it and continue
            return LLMResponse(content="", model=self.model, provider="openai", error=str(e))
