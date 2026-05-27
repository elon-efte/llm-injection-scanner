"""
scanner/adapters/__init__.py

Makes all adapters importable from scanner.adapters directly.

Example:
    from scanner.adapters import OpenAIAdapter, AnthropicAdapter
"""

from .base import BaseLLMAdapter, LLMResponse
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .ollama_adapter import OllamaAdapter
from .generic_adapter import GenericAdapter

__all__ = [
    "BaseLLMAdapter",
    "LLMResponse",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "OllamaAdapter",
    "GenericAdapter",
]
