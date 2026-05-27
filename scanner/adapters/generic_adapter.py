"""
generic_adapter.py — Adapter for any OpenAI-compatible API endpoint.

Many LLM providers (Together AI, Groq, Mistral AI, local LM Studio, etc.)
implement the same API format as OpenAI. This adapter works with all of them
by letting you set a custom base URL.

Requirements:
    pip install openai   (the openai library supports custom base URLs)

Usage:
    from scanner.adapters.generic_adapter import GenericAdapter

    # Example: Groq
    adapter = GenericAdapter(
        api_key="gsk_...",
        model="llama3-8b-8192",
        base_url="https://api.groq.com/openai/v1"
    )

    # Example: LM Studio (running locally on port 1234)
    adapter = GenericAdapter(
        api_key="lm-studio",   # LM Studio doesn't need a real key
        model="local-model",
        base_url="http://localhost:1234/v1"
    )
"""

from .base import BaseLLMAdapter, LLMResponse


class GenericAdapter(BaseLLMAdapter):
    """
    Works with any OpenAI-compatible API.
    Just point it at a different base_url.
    """

    def __init__(self, api_key: str, model: str, base_url: str, provider_name: str = "generic"):
        """
        Args:
            api_key:       API key for the provider (use any string for APIs that don't need one)
            model:         Model name as expected by the provider
            base_url:      The API base URL (e.g. "https://api.groq.com/openai/v1")
            provider_name: A label for this provider shown in reports
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self._provider_name = provider_name

    @property
    def name(self) -> str:
        return f"{self._provider_name}/{self.model}"

    def send(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Send a chat message using the OpenAI-compatible API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                temperature=0,
                max_tokens=1024,
            )
            content = response.choices[0].message.content or ""
            return LLMResponse(content=content, model=self.model, provider=self._provider_name)

        except Exception as e:
            return LLMResponse(content="", model=self.model, provider=self._provider_name, error=str(e))
