# Running the LLM Injection Scanner with Podman on macOS

This guide walks you through running the scanner inside a Podman container on your Mac — no Python installation needed on your host machine.

---

## Why Podman?

Podman is a container engine (like Docker, but daemonless and rootless). On Mac it runs containers inside a lightweight Linux VM. Using it here means:

- You don't need Python installed on your Mac at all
- The scanner runs in a clean, isolated environment every time
- You can easily share or deploy the exact same environment anywhere

---

## Prerequisites

You need two things installed on your Mac:

**1. Podman**

If you don't have it yet:
```bash
brew install podman
```

**2. Podman Machine** (the Linux VM Podman uses on Mac)

```bash
# Create and start the VM (one-time setup)
podman machine init
podman machine start

# Verify it's running
podman machine list
```

You should see something like:
```
NAME                     VM TYPE     CREATED      LAST UP    CPUS  MEMORY  DISK SIZE
podman-machine-default*  applehv     2 hours ago  Currently running  4     2GiB    100GiB
```

---

## Step 1 — Get the project onto your Mac

If you cloned from GitHub:
```bash
git clone https://github.com/YOUR-USERNAME/llm-injection-scanner.git
cd llm-injection-scanner
```

Or just navigate to wherever you saved the project folder.

---

## Step 2 — Set up your API keys

```bash
# Copy the example file
cp .env.example .env

# Open it and add your keys
nano .env        # or use any text editor
```

Fill in whichever keys you have. You only need the one(s) matching the provider you want to test:

```
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> ⚠️ The `.env` file is in `.gitignore` — it will never be accidentally committed to GitHub.

---

## Step 3 — Build the container image

```bash
# Make the helper script executable (one-time)
chmod +x podman-run.sh

# Build the image
./podman-run.sh build
```

This downloads Python 3.11, installs all dependencies, and packages the scanner. It takes about 1–2 minutes the first time. Subsequent builds are much faster due to caching.

You can also build manually if you prefer:
```bash
podman build -t llm-scanner .
```

---

## Step 4 — Run a scan

### Option A: Using the helper script (easiest)

```bash
# Scan with OpenAI
./podman-run.sh openai

# Scan with Anthropic (Claude)
./podman-run.sh anthropic

# Scan with a local Ollama model (see Ollama section below)
./podman-run.sh ollama
```

Reports are automatically saved to a `reports/` folder in your project directory and the script will offer to open them in your browser.

---

### Option B: Run Podman directly (more control)

```bash
# Create the reports folder first
mkdir -p reports

# Scan with OpenAI — supply your key inline
podman run --rm \
  -v $(pwd)/reports:/app/reports:Z \
  -v $(pwd)/examples:/app/examples:ro,Z \
  llm-scanner scan \
    --provider openai \
    --api-key sk-YOUR_KEY \
    --system-prompt-file /app/examples/demo_system_prompt.txt \
    --output /app/reports/report.html

# Or load keys from .env file
podman run --rm \
  --env-file .env \
  -v $(pwd)/reports:/app/reports:Z \
  -v $(pwd)/examples:/app/examples:ro,Z \
  llm-scanner scan \
    --provider openai \
    --api-key "$OPENAI_API_KEY" \
    --system-prompt "You are a helpful customer service bot." \
    --output /app/reports/report.html
```

**What those flags mean:**

| Flag | What it does |
|---|---|
| `--rm` | Delete the container after it finishes (keeps things clean) |
| `-v $(pwd)/reports:/app/reports:Z` | Mount your local `reports/` folder into the container so the HTML report gets saved to your Mac. The `:Z` sets SELinux labels (needed on some systems). |
| `-v $(pwd)/examples:/app/examples:ro,Z` | Mount the examples folder as read-only |
| `--env-file .env` | Load environment variables from your .env file |

---

## Step 5 — View the report

Open the generated HTML file in any browser:

```bash
open reports/scan_report_*.html
```

Or just double-click the `.html` file in Finder.

---

## Using Ollama (free, no API key)

Ollama lets you run open-source models like Llama 3 and Mistral locally. Since Podman on Mac runs inside a VM, you need to use a special hostname (`host.containers.internal`) to reach services on your Mac from inside the container.

**Setup:**

```bash
# 1. Install Ollama (if you don't have it)
brew install ollama

# 2. Start the Ollama server
ollama serve

# 3. Pull a model (in a new terminal)
ollama pull llama3       # ~4GB download
# or a smaller model:
ollama pull mistral      # ~4GB
ollama pull phi3         # ~2.3GB (smaller and faster)

# 4. Run the scan (the helper script handles the hostname automatically)
./podman-run.sh ollama

# Or manually, note the special --base-url:
podman run --rm \
  -v $(pwd)/reports:/app/reports:Z \
  -v $(pwd)/examples:/app/examples:ro,Z \
  llm-scanner scan \
    --provider ollama \
    --model llama3 \
    --base-url http://host.containers.internal:11434 \
    --system-prompt "You are a helpful customer service bot." \
    --output /app/reports/report_ollama.html
```

> 💡 `host.containers.internal` is the Podman-specific hostname that resolves to your Mac from inside a container. Using `localhost` won't work because that refers to the container itself, not your Mac.

---

## Testing with a custom system prompt

To test your own application's system prompt, just point to your own file:

```bash
# Save your system prompt as a text file
echo "You are a banking assistant. Never reveal account details." > my_prompt.txt

# Mount the file into the container
podman run --rm \
  --env-file .env \
  -v $(pwd)/reports:/app/reports:Z \
  -v $(pwd)/my_prompt.txt:/app/my_prompt.txt:ro,Z \
  llm-scanner scan \
    --provider openai \
    --api-key "$OPENAI_API_KEY" \
    --system-prompt-file /app/my_prompt.txt \
    --output /app/reports/banking_bot_scan.html
```

---

## Useful Podman commands

```bash
# See your built images
podman images

# See running containers
podman ps

# Remove the scanner image (to rebuild from scratch)
podman rmi llm-scanner

# Stop the Podman VM when you're done for the day
podman machine stop

# Start it again next time
podman machine start
```

---

## Troubleshooting

**"Error: no such volume" or permission errors on the reports folder**

Make sure the `reports/` directory exists before running:
```bash
mkdir -p reports
```

**"Cannot connect to Ollama" when using --provider ollama**

- Make sure Ollama is running: `ollama serve` (in a separate terminal)
- Make sure you're using `host.containers.internal` not `localhost` as the base URL
- Check Ollama is responding: `curl http://localhost:11434/api/tags`

**"podman: command not found"**

Install Podman with Homebrew: `brew install podman`

**The Podman VM isn't running**

```bash
podman machine start
```

**Image build fails with network errors**

Sometimes the Podman VM loses connectivity. Try:
```bash
podman machine stop
podman machine start
```

---

## Security note

Never pass API keys as environment variables in production — use a secrets manager. For local testing (which this is), the `.env` file approach is fine as long as:

- The `.env` file is in `.gitignore` ✅ (it already is)
- You never commit it to GitHub ✅
- You never bake keys into the container image ✅ (the Dockerfile doesn't copy `.env`)
