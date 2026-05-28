"""
__main__.py — Allows running the scanner as a module.

This file lets you invoke the scanner with:
    python -m scanner <command>

instead of having to run scanner/cli.py directly.
"""

from .cli import cli

if __name__ == "__main__":
    cli()
