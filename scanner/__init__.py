"""
scanner — LLM Prompt Injection Scanner

A security testing toolkit for detecting prompt injection vulnerabilities
in LLM-based applications. Based on OWASP LLM Top 10.

Quick usage:
    from scanner.adapters import OpenAIAdapter
    from scanner.core import Scanner

    adapter = OpenAIAdapter(api_key="sk-...", model="gpt-3.5-turbo")
    scanner = Scanner(adapter=adapter)
    result = scanner.run(system_prompt="You are a helpful bot.")
"""

__version__ = "1.0.0"
__author__  = "Your Name"
