# ============================================================
# LLM Injection Scanner — Dockerfile
# ============================================================
# Builds a lean Python 3.11 image with all scanner dependencies.
#
# Build:
#   podman build -t llm-scanner .
#
# Run (OpenAI example):
#   podman run --rm \
#     -e OPENAI_API_KEY=sk-... \
#     -v $(pwd)/reports:/app/reports \
#     llm-scanner scan \
#       --provider openai \
#       --api-key $OPENAI_API_KEY \
#       --system-prompt "You are a helpful bot." \
#       --output /app/reports/report.html
# ============================================================

# --- Stage 1: Use a slim official Python image ---
# python:3.11-slim is much smaller than the full image (~50MB vs ~300MB)
FROM python:3.11-slim

# Set a working directory inside the container
WORKDIR /app

# --- Stage 2: Install system dependencies ---
# We need curl only to do a health-check ping to Ollama (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# --- Stage 3: Install Python dependencies ---
# Copy requirements first so Docker/Podman can cache this layer.
# If you only change source code (not requirements.txt), the pip install
# step is skipped on rebuilds — much faster.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 4: Copy the application source code ---
COPY scanner/ ./scanner/
COPY examples/ ./examples/

# Create a folder inside the container where reports will be saved.
# This will be mounted to a folder on your Mac (see run instructions).
RUN mkdir -p /app/reports

# --- Stage 5: Set the default entrypoint ---
# This means you can run: podman run llm-scanner scan --help
# instead of: podman run llm-scanner python -m scanner scan --help
ENTRYPOINT ["python", "-m", "scanner"]

# Default command if you run `podman run llm-scanner` with no arguments
CMD ["--help"]
