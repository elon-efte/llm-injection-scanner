# 🔬 LLM Prompt Injection Scanner

[![CI](https://github.com/YOUR-USERNAME/llm-injection-scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/llm-injection-scanner/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![OWASP LLM Top 10](https://img.shields.io/badge/OWASP-LLM%20Top%2010-red)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
[![Docker Ready](https://img.shields.io/badge/container-Podman%20%2F%20Docker-blue)](PODMAN.md)

> An automated security testing tool for detecting **prompt injection vulnerabilities** in LLM-powered applications.  
> Based on the [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

---

## Demo Report

> Below is a sample scan against a simulated vulnerable model. Open [demo_report.html](demo_report.html) in your browser to see the full interactive report.

![Report screenshot — summary showing CRITICAL risk, 14 vulnerable, 3 suspicious](docs/report-screenshot.png)

---

---

## What Is This?

When companies build chatbots, copilots, or AI agents using LLMs like GPT-4 or Claude, they give the model a **system prompt** — a set of secret instructions that define the bot's behaviour, restrictions, and identity.

**Prompt injection** is an attack where a malicious user sends crafted input designed to:
- Override or ignore those system instructions
- Extract the hidden system prompt
- Make the model adopt a new unrestricted persona (jailbreak)
- Leak sensitive data from the model's context

This scanner automates that testing. You point it at an LLM + system prompt, it runs a library of attack payloads, and generates a professional HTML report showing which attacks succeeded.

---

## Features

- **21 attack payloads** across 6 OWASP LLM Top 10 categories
- **4 LLM backends**: OpenAI, Anthropic (Claude), Ollama (local), and any OpenAI-compatible API
- **Automatic detection** using keyword matching + semantic pattern analysis
- **Professional HTML report** with severity ratings, confidence scores, and per-test details
- **CI/CD ready**: exits with code 2 if vulnerabilities are found (triggers pipeline failures)
- **Beginner-friendly**: every file is thoroughly commented

---

## Attack Categories

| Category | # Payloads | OWASP Ref |
|---|---|---|
| Direct Prompt Injection | 5 | LLM01 |
| System Prompt Extraction | 5 | LLM01, LLM07 |
| Jailbreaks / Role Override | 5 | LLM01 |
| Indirect Prompt Injection | 3 | LLM01 |
| Data Exfiltration | 3 | LLM06 |
| Instruction Boundary Tests | 3 | LLM01 |

---

## Project Structure

```
llm-injection-scanner/
│
├── scanner/                    # Main Python package
│   ├── __init__.py
│   ├── __main__.py             # Allows `python -m scanner` invocation
│   ├── cli.py                  # Command-line interface (built with Click)
│   ├── core.py                 # Scanner engine — orchestrates the scan
│   ├── payloads.py             # Attack payload library (21 payloads)
│   ├── detectors.py            # Response analysis & verdict logic
│   ├── reporter.py             # HTML report generator
│   └── adapters/
│       ├── base.py             # Abstract base class for all adapters
│       ├── openai_adapter.py   # OpenAI GPT adapter
│       ├── anthropic_adapter.py # Anthropic Claude adapter
│       ├── ollama_adapter.py   # Local Ollama adapter
│       └── generic_adapter.py  # Any OpenAI-compatible API
│
├── examples/
│   └── demo_system_prompt.txt  # Example system prompt for testing
│
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR-USERNAME/llm-injection-scanner.git
cd llm-injection-scanner
pip install -r requirements.txt
```

### 2. Run a scan

**Against OpenAI:**
```bash
python -m scanner scan \
  --provider openai \
  --api-key sk-YOUR_KEY_HERE \
  --system-prompt "You are a helpful customer service bot for AcmeCorp."
```

**Against Anthropic (Claude):**
```bash
python -m scanner scan \
  --provider anthropic \
  --api-key sk-ant-YOUR_KEY_HERE \
  --model claude-3-haiku-20240307 \
  --system-prompt "You are a helpful customer service bot."
```

**Against a local Ollama model (free, no API key):**
```bash
# First install Ollama and pull a model:
#   https://ollama.ai → then run: ollama pull llama3

python -m scanner scan \
  --provider ollama \
  --model llama3 \
  --system-prompt "You are a helpful customer service bot."
```

**Load system prompt from a file:**
```bash
python -m scanner scan \
  --provider openai \
  --api-key sk-... \
  --system-prompt-file examples/demo_system_prompt.txt
```

### 3. Open the report

The scanner saves `scan_report_<timestamp>.html` to the current directory. Open it in any browser for the full interactive report.

---

## CLI Reference

```
python -m scanner --help
python -m scanner scan --help
python -m scanner list-payloads
```

### `scan` options

| Option | Short | Description |
|---|---|---|
| `--provider` | `-p` | `openai`, `anthropic`, `ollama`, `generic` |
| `--api-key` | `-k` | API key for OpenAI or Anthropic |
| `--model` | `-m` | Model name (defaults per provider) |
| `--system-prompt` | `-s` | System prompt text in quotes |
| `--system-prompt-file` | `-f` | Path to .txt file with system prompt |
| `--output` | `-o` | Custom output path for HTML report |
| `--categories` | `-c` | Run only specific categories (repeatable) |
| `--severity` | `-v` | Minimum severity: `critical`, `high`, `medium`, `low` |
| `--delay` | `-d` | Seconds between API calls (default: 0.5) |
| `--quiet` | `-q` | Suppress progress output |

### Filter examples

```bash
# Run only critical and high severity payloads
python -m scanner scan -p openai -k sk-... -s "..." --severity high

# Run only jailbreak and direct injection tests
python -m scanner scan -p openai -k sk-... -s "..." \
  -c "Jailbreaks" -c "Direct Injection"

# List all available payloads
python -m scanner list-payloads
```

---

## Use as a Python Library

You can also import the scanner directly into your own Python scripts:

```python
from scanner.adapters import OpenAIAdapter, AnthropicAdapter, OllamaAdapter
from scanner.core import Scanner
from scanner.payloads import ALL_PAYLOADS, JAILBREAKS
from scanner.reporter import generate_report

# Choose your adapter
adapter = OpenAIAdapter(api_key="sk-...", model="gpt-3.5-turbo")

# Run the scan (you can pass a subset of payloads)
scanner = Scanner(adapter=adapter, payloads=JAILBREAKS)
result = scanner.run(system_prompt="You are a helpful bot.")

# Generate the HTML report
report_path = generate_report(result, output_path="my_report.html")
print(f"Report saved: {report_path}")

# Access results programmatically
for r in result.results:
    print(f"{r.payload_id}: {r.verdict.value} (confidence: {r.confidence:.0%})")
```

---

## Adding Custom Payloads

Add your own payloads to `scanner/payloads.py`:

```python
from scanner.payloads import Payload, Severity, ALL_PAYLOADS

my_payload = Payload(
    id="CUSTOM-001",
    name="My Custom Injection",
    category="LLM01 - Direct Prompt Injection",
    severity=Severity.HIGH,
    payload="[Your injection text here]",
    description="What this attack attempts to do.",
    detection_hints=["keyword that appears if attack succeeds"],
)

# Add to the master list
ALL_PAYLOADS.append(my_payload)
```

---

## Adding a New LLM Adapter

To add support for a new LLM backend, create a file in `scanner/adapters/` and subclass `BaseLLMAdapter`:

```python
from scanner.adapters.base import BaseLLMAdapter, LLMResponse

class MyNewAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @property
    def name(self) -> str:
        return f"my-provider/{self.model}"

    def send(self, system_prompt: str, user_message: str) -> LLMResponse:
        # ... call your API here ...
        return LLMResponse(content=response_text, model=self.model, provider="my-provider")
```

---

## CI/CD Integration

The scanner exits with code `2` if any vulnerabilities are found. Use this in GitHub Actions to block merges:

```yaml
# .github/workflows/llm-security.yml
name: LLM Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: |
          python -m scanner scan \
            --provider openai \
            --api-key ${{ secrets.OPENAI_API_KEY }} \
            --severity high \
            --system-prompt-file examples/demo_system_prompt.txt
```

---

## References

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [Prompt Injection Attacks and Defenses](https://arxiv.org/abs/2302.12173)
- [Gandalf by Lakera — Prompt Injection Game](https://gandalf.lakera.ai/)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built as a security research project. Only use against systems you own or have explicit permission to test.*
