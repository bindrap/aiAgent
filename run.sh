#!/bin/bash

# Terminal Voice AI Agent Launcher for Arch Linux + AMD GPU

cd /home/parteek/Documents/aiAgent

# Activate Python virtual environment
source venv/bin/activate

# Prefer the CMake build output; fall back to legacy location if present
WHISPER_BIN_DEFAULT="./whisper.cpp/build/bin/whisper-cli"
WHISPER_BIN_LEGACY="./whisper.cpp/build/bin/main"
WHISPER_BIN="${WHISPER_BIN:-$WHISPER_BIN_DEFAULT}"

if [ ! -x "$WHISPER_BIN" ]; then
  if [ -x "$WHISPER_BIN_LEGACY" ]; then
    WHISPER_BIN="$WHISPER_BIN_LEGACY"
  else
    echo "whisper.cpp binary not found at $WHISPER_BIN or $WHISPER_BIN_LEGACY." >&2
    echo "Run ./setup-whisper-rocm.sh or build whisper.cpp manually first." >&2
    exit 1
  fi
fi

# Optional: Set ROCm environment variables for AMD 7800XT
# export HSA_OVERRIDE_GFX_VERSION=11.0.0  # Uncomment if needed

# Run the voice agent
python -m voice \
  --model llama3.1:8b \
  --whisper-binary "$WHISPER_BIN" \
  --whisper-model ./whisper.cpp/models/ggml-base.en.bin \
  --threads 8 \
  --system "You are a helpful AI assistant. Be concise and clear." \
  "$@"

# Note: Add "$@" to pass additional command-line arguments
# Example: ./run.sh --keep-recordings
