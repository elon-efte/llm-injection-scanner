"""
cli.py — Command-line interface for the LLM Injection Scanner.

Uses the `click` library to provide a clean CLI experience.

Basic usage:
    python -m scanner scan --provider openai --api-key sk-... --system-prompt "You are a helpful bot."

Full help:
    python -m scanner --help
    python -m scanner scan --help
"""

import sys
from pathlib import Path
from datetime import datetime

try:
    import click
except ImportError:
    print("ERROR: 'click' is not installed. Run: pip install click")
    sys.exit(1)

from .adapters import OpenAIAdapter, AnthropicAdapter, OllamaAdapter, GenericAdapter
from .core import Scanner
from .payloads import ALL_PAYLOADS, PAYLOAD_CATEGORIES, Severity
from .reporter import generate_report


# =============================================================================
# Main CLI group
# =============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="LLM Injection Scanner")
def cli():
    """
    🔬 LLM Prompt Injection Scanner

    Automated security testing tool for LLM applications.
    Detects vulnerabilities based on OWASP LLM Top 10.

    \b
    Quick start:
      # Test with OpenAI
      python -m scanner scan --provider openai --api-key sk-... \\
          --system-prompt "You are a helpful assistant."

      # Test with a local Ollama model
      python -m scanner scan --provider ollama --model llama3 \\
          --system-prompt "You are a helpful assistant."
    """
    pass


# =============================================================================
# scan command
# =============================================================================

@cli.command()
@click.option("--provider", "-p",
    type=click.Choice(["openai", "anthropic", "ollama", "generic"], case_sensitive=False),
    required=True,
    help="Which LLM provider to test against.")
@click.option("--api-key", "-k",
    default=None,
    help="API key for OpenAI or Anthropic. Not needed for Ollama.")
@click.option("--model", "-m",
    default=None,
    help="Model name. Defaults: openai=gpt-3.5-turbo, anthropic=claude-3-haiku-20240307, ollama=llama3")
@click.option("--base-url",
    default=None,
    help="(generic provider only) Custom API base URL, e.g. https://api.groq.com/openai/v1")
@click.option("--system-prompt", "-s",
    default=None,
    help="The system prompt to test. Wrap in quotes.")
@click.option("--system-prompt-file", "-f",
    default=None, type=click.Path(exists=True),
    help="Path to a .txt file containing the system prompt (use this for long prompts).")
@click.option("--output", "-o",
    default=None,
    help="Output path for the HTML report. Defaults to: scan_report_<timestamp>.html")
@click.option("--categories", "-c",
    multiple=True,
    type=click.Choice(list(PAYLOAD_CATEGORIES.keys()), case_sensitive=False),
    help="Run only specific payload categories. Can be used multiple times.")
@click.option("--severity", "-v",
    default=None,
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Run only payloads at or above this severity level.")
@click.option("--delay", "-d",
    default=0.5, type=float,
    help="Seconds to wait between API calls (avoids rate limiting). Default: 0.5")
@click.option("--quiet", "-q",
    is_flag=True, default=False,
    help="Suppress progress output. Only show the final summary.")
def scan(provider, api_key, model, base_url, system_prompt, system_prompt_file,
         output, categories, severity, delay, quiet):
    """
    Run a prompt injection scan against a target LLM.

    \b
    Examples:
      # Basic OpenAI scan
      python -m scanner scan -p openai -k sk-... -s "You are a customer service bot."

      # Scan with a system prompt from a file
      python -m scanner scan -p anthropic -k sk-ant-... -f examples/demo_system_prompt.txt

      # Scan only high-severity payloads
      python -m scanner scan -p ollama --severity high -s "You are a helpful assistant."

      # Run only injection and jailbreak categories
      python -m scanner scan -p openai -k sk-... \\
          -c "Direct Injection" -c "Jailbreaks" -s "You are a bot."
    """

    # --- Load system prompt ---
    if system_prompt_file:
        prompt_text = Path(system_prompt_file).read_text(encoding="utf-8").strip()
        click.echo(f"📄 Loaded system prompt from: {system_prompt_file}")
    elif system_prompt:
        prompt_text = system_prompt
    else:
        click.echo("❌ Error: You must provide either --system-prompt or --system-prompt-file")
        sys.exit(1)

    # --- Build adapter ---
    adapter = _build_adapter(provider, api_key, model, base_url)

    # --- Filter payloads ---
    payloads = list(ALL_PAYLOADS)

    if categories:
        payloads = [
            p for p in payloads
            if any(cat.lower() in p.category.lower() for cat in categories)
        ]

    if severity:
        severity_order = ["low", "medium", "high", "critical"]
        min_index = severity_order.index(severity.lower())
        payloads = [
            p for p in payloads
            if severity_order.index(p.severity.value) >= min_index
        ]

    if not payloads:
        click.echo("❌ Error: No payloads match your filters. Try relaxing --categories or --severity.")
        sys.exit(1)

    click.echo(f"🔬 Running {len(payloads)} payload(s) against {adapter.name}...\n")

    # --- Run scan ---
    scanner = Scanner(adapter=adapter, payloads=payloads, delay_seconds=delay, verbose=not quiet)
    result = scanner.run(system_prompt=prompt_text)

    # --- Generate report ---
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"scan_report_{timestamp}.html"

    report_path = generate_report(result, output_path=output)
    click.echo(f"\n✅ Report saved to: {report_path}")
    click.echo(f"   Open it in your browser to view the full results.\n")

    # Exit with non-zero code if vulnerabilities were found
    # (useful for CI/CD pipelines — a non-zero exit triggers a pipeline failure)
    if result.vulnerable_count > 0:
        sys.exit(2)


# =============================================================================
# list-payloads command
# =============================================================================

@cli.command(name="list-payloads")
@click.option("--category", "-c", default=None, help="Filter by category name.")
def list_payloads(category):
    """List all available payloads and their metadata."""
    payloads = list(ALL_PAYLOADS)
    if category:
        payloads = [p for p in payloads if category.lower() in p.category.lower()]

    current_cat = None
    for p in payloads:
        if p.category != current_cat:
            current_cat = p.category
            click.echo(f"\n  📁 {current_cat}")
            click.echo("  " + "─" * 50)
        severity_color = {
            "critical": "\033[91m",  # red
            "high":     "\033[93m",  # yellow
            "medium":   "\033[94m",  # blue
            "low":      "\033[92m",  # green
        }.get(p.severity.value, "")
        reset = "\033[0m"
        click.echo(f"  {p.id:<10} {severity_color}[{p.severity.value.upper():8}]{reset}  {p.name}")

    click.echo(f"\n  Total: {len(payloads)} payloads\n")


# =============================================================================
# Adapter factory
# =============================================================================

def _build_adapter(provider: str, api_key: str, model: str, base_url: str):
    """Create the appropriate adapter based on CLI flags."""
    provider = provider.lower()

    if provider == "openai":
        if not api_key:
            click.echo("❌ Error: --api-key is required for OpenAI. Get one at https://platform.openai.com")
            sys.exit(1)
        return OpenAIAdapter(api_key=api_key, model=model or "gpt-3.5-turbo")

    elif provider == "anthropic":
        if not api_key:
            click.echo("❌ Error: --api-key is required for Anthropic. Get one at https://console.anthropic.com")
            sys.exit(1)
        return AnthropicAdapter(api_key=api_key, model=model or "claude-3-haiku-20240307")

    elif provider == "ollama":
        return OllamaAdapter(
            model=model or "llama3",
            base_url=base_url or "http://localhost:11434"
        )

    elif provider == "generic":
        if not api_key or not base_url:
            click.echo("❌ Error: --api-key and --base-url are required for the generic provider.")
            sys.exit(1)
        return GenericAdapter(
            api_key=api_key,
            model=model or "default",
            base_url=base_url,
        )


# =============================================================================
# Module entry point
# =============================================================================

if __name__ == "__main__":
    cli()
