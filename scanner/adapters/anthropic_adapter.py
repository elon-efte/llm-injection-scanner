"""
anthropic_adapter.py — Adapter for Anthropic's Claude models.

Requirements:
    pip install anthropic

Usage:
    from scanner.adapters.anthropic_adapter import AnthropicAdapter
    adapter = AnthropicAdapter(api_key="sk-ant-...", model="claude-3-haiku-20240307")
"""

from .base import BaseLLMAdapter, LLMResponse


class AnthropicAdapter(BaseLLMAdapter):
    """Sends prompts to Anthropic's Claude via the Messages API."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """
        Args:
            api_key: Your Anthropic API key (starts with sk-ant-...)
            model:   Which Claude model to use.
                     "claude-3-haiku-20240307"  — fast and cheap, good for bulk testing
                     "claude-3-sonnet-20240229" — balanced
                     "claude-3-opus-20240229"   — most capable
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    @property
    def name(self) -> str:
        return f"anthropic/{self.model}"

    def send(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Send a message to Claude and return the response."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,          # Claude uses a dedicated `system` parameter
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )
            content = response.content[0].text if response.content else ""
            return LLMResponse(content=content, model=self.model, provider="anthropic")

        except Exception as e:
            return LLMResponse(content="", model=self.model, provider="anthropic", error=str(e))
