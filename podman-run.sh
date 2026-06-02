#!/usr/bin/env bash
# ============================================================
# podman-run.sh — Helper script for running the LLM Scanner
#                 with Podman on macOS
# ============================================================
# Usage:
#   chmod +x podman-run.sh          # Make executable (first time only)
#   ./podman-run.sh build           # Build the container image
#   ./podman-run.sh openai          # Scan with OpenAI
#   ./podman-run.sh anthropic       # Scan with Anthropic (Claude)
#   ./podman-run.sh ollama          # Scan with local Ollama
#   ./podman-run.sh list            # List all available payloads
# ============================================================

set -e  # Exit immediately if any command fails

# --- Configuration — edit these to match your setup ---
IMAGE_NAME="llm-scanner"
REPORTS_DIR="$(pwd)/reports"           # Reports will be saved here on your Mac
SYSTEM_PROMPT_FILE="examples/demo_system_prompt.txt"

# ============================================================
# Helper: create reports folder if it doesn't exist
# ============================================================
ensure_reports_dir() {
    mkdir -p "$REPORTS_DIR"
    echo "📁 Reports will be saved to: $REPORTS_DIR"
}

# ============================================================
# BUILD — compile the container image
# ============================================================
cmd_build() {
    echo "🔨 Building container image: $IMAGE_NAME ..."
    podman build -t "$IMAGE_NAME" .
    echo ""
    echo "✅ Build complete. Image '$IMAGE_NAME' is ready."
    echo "   Run './podman-run.sh openai' to start a scan."
}

# ============================================================
# OPENAI — scan using OpenAI GPT models
# ============================================================
cmd_openai() {
    # Load API key from .env file if it exists
    if [ -f ".env" ]; then
        source .env
    fi

    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ Error: OPENAI_API_KEY is not set."
        echo "   Either:"
        echo "   1. Copy .env.example to .env and add your key, OR"
        echo "   2. Run: export OPENAI_API_KEY=sk-your-key-here"
        exit 1
    fi

    ensure_reports_dir

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REPORT_FILE="scan_openai_${TIMESTAMP}.html"

    echo "🔬 Running scan against OpenAI (gpt-3.5-turbo)..."
    echo ""

    podman run --rm \
        -e OPENAI_API_KEY="$OPENAI_API_KEY" \
        -v "$REPORTS_DIR":/app/reports:Z \
        -v "$(pwd)/examples":/app/examples:ro,Z \
        "$IMAGE_NAME" scan \
            --provider openai \
            --api-key "$OPENAI_API_KEY" \
            --system-prompt-file "/app/examples/demo_system_prompt.txt" \
            --output "/app/reports/${REPORT_FILE}"

    echo ""
    echo "📄 Report saved: $REPORTS_DIR/$REPORT_FILE"
    echo "   Open it in Safari or Chrome to view results."

    # Optionally open the report automatically on Mac
    if command -v open &>/dev/null; then
        read -p "   Open report in browser now? (y/n): " yn
        if [ "$yn" = "y" ]; then
            open "$REPORTS_DIR/$REPORT_FILE"
        fi
    fi
}

# ============================================================
# ANTHROPIC — scan using Anthropic Claude
# ============================================================
cmd_anthropic() {
    if [ -f ".env" ]; then
        source .env
    fi

    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ Error: ANTHROPIC_API_KEY is not set."
        echo "   Copy .env.example to .env and add your Anthropic key."
        exit 1
    fi

    ensure_reports_dir

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REPORT_FILE="scan_anthropic_${TIMESTAMP}.html"

    echo "🔬 Running scan against Anthropic (claude-3-haiku)..."
    echo ""

    podman run --rm \
        -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
        -v "$REPORTS_DIR":/app/reports:Z \
        -v "$(pwd)/examples":/app/examples:ro,Z \
        "$IMAGE_NAME" scan \
            --provider anthropic \
            --api-key "$ANTHROPIC_API_KEY" \
            --model "claude-3-haiku-20240307" \
            --system-prompt-file "/app/examples/demo_system_prompt.txt" \
            --output "/app/reports/${REPORT_FILE}"

    echo ""
    echo "📄 Report saved: $REPORTS_DIR/$REPORT_FILE"

    if command -v open &>/dev/null; then
        read -p "   Open report in browser now? (y/n): " yn
        if [ "$yn" = "y" ]; then
            open "$REPORTS_DIR/$REPORT_FILE"
        fi
    fi
}

# ============================================================
# OLLAMA — scan using a local Ollama model (no API key needed)
#
# IMPORTANT for Mac + Podman:
#   Podman runs in a VM on Mac. To reach Ollama on your Mac from
#   inside the container, use 'host.containers.internal' instead
#   of 'localhost'. This script handles that automatically.
# ============================================================
cmd_ollama() {
    OLLAMA_MODEL="${1:-llama3}"   # Default to llama3, override with: ./podman-run.sh ollama mistral

    # Check if Ollama is running on the host
    if ! curl -s --max-time 2 "http://localhost:11434/api/tags" > /dev/null 2>&1; then
        echo "❌ Error: Ollama doesn't appear to be running."
        echo "   Start it with: ollama serve"
        echo "   Then pull a model: ollama pull $OLLAMA_MODEL"
        exit 1
    fi

    ensure_reports_dir

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REPORT_FILE="scan_ollama_${OLLAMA_MODEL}_${TIMESTAMP}.html"

    echo "🔬 Running scan against local Ollama model: $OLLAMA_MODEL ..."
    echo "   (Connecting to Ollama on your Mac via host.containers.internal)"
    echo ""

    podman run --rm \
        -v "$REPORTS_DIR":/app/reports:Z \
        -v "$(pwd)/examples":/app/examples:ro,Z \
        "$IMAGE_NAME" scan \
            --provider ollama \
            --model "$OLLAMA_MODEL" \
            --base-url "http://host.containers.internal:11434" \
            --system-prompt-file "/app/examples/demo_system_prompt.txt" \
            --output "/app/reports/${REPORT_FILE}"

    echo ""
    echo "📄 Report saved: $REPORTS_DIR/$REPORT_FILE"

    if command -v open &>/dev/null; then
        read -p "   Open report in browser now? (y/n): " yn
        if [ "$yn" = "y" ]; then
            open "$REPORTS_DIR/$REPORT_FILE"
        fi
    fi
}

# ============================================================
# LIST — show all available payloads
# ============================================================
cmd_list() {
    podman run --rm "$IMAGE_NAME" list-payloads
}

# ============================================================
# CUSTOM — run with your own flags (pass through to the scanner)
# ============================================================
cmd_custom() {
    ensure_reports_dir
    podman run --rm \
        -v "$REPORTS_DIR":/app/reports:Z \
        -v "$(pwd)/examples":/app/examples:ro,Z \
        "$IMAGE_NAME" "$@"
}

# ============================================================
# Main — route to the right command
# ============================================================
COMMAND="${1:-help}"

case "$COMMAND" in
    build)      cmd_build ;;
    openai)     cmd_openai ;;
    anthropic)  cmd_anthropic ;;
    ollama)     cmd_ollama "${2:-llama3}" ;;
    list)       cmd_list ;;
    custom)     shift; cmd_custom "$@" ;;
    help|--help|-h)
        echo ""
        echo "  🔬 LLM Injection Scanner — Podman Helper"
        echo ""
        echo "  Usage: ./podman-run.sh <command>"
        echo ""
        echo "  Commands:"
        echo "    build      Build the container image (run this first)"
        echo "    openai     Scan using OpenAI (needs OPENAI_API_KEY in .env)"
        echo "    anthropic  Scan using Anthropic Claude (needs ANTHROPIC_API_KEY in .env)"
        echo "    ollama     Scan using local Ollama (ollama must be running on your Mac)"
        echo "    list       List all available attack payloads"
        echo "    custom     Pass custom flags directly, e.g.:"
        echo "               ./podman-run.sh custom scan --provider openai --help"
        echo ""
        echo "  Setup:"
        echo "    1. cp .env.example .env   # Add your API keys"
        echo "    2. ./podman-run.sh build  # Build the image"
        echo "    3. ./podman-run.sh openai # Run your first scan"
        echo ""
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "   Run './podman-run.sh help' for usage."
        exit 1
        ;;
esac
