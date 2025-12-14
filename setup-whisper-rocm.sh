#!/bin/bash
set -e

echo "=== Setting up whisper.cpp with ROCm support for AMD GPU ==="

cd /home/parteek/Documents/aiAgent

# Clone whisper.cpp if not already present
if [ ! -d "whisper.cpp" ]; then
    echo "Cloning whisper.cpp..."
    git clone https://github.com/ggerganov/whisper.cpp.git
else
    echo "whisper.cpp directory already exists, updating..."
    cd whisper.cpp
    git pull
    cd ..
fi

cd whisper.cpp

# Clean previous builds
echo "Cleaning previous builds..."
make clean 2>/dev/null || true

# Build with ROCm/HIP support for AMD GPUs
echo "Building with ROCm/HIP support..."
echo "This may take a few minutes..."
make GGML_HIPBLAS=1

# Check if build was successful (CMake places binaries in build/bin)
WHISPER_BIN="./build/bin/whisper-cli"
LEGACY_BIN="./build/bin/main"
DIRECT_BIN="./main"
if [ -x "$WHISPER_BIN" ]; then
    echo "✓ Build successful! Binary at $WHISPER_BIN"
elif [ -x "$LEGACY_BIN" ]; then
    WHISPER_BIN="$LEGACY_BIN"
    echo "✓ Build successful! Binary at $WHISPER_BIN (deprecated; prefer whisper-cli)"
elif [ -x "$DIRECT_BIN" ]; then
    WHISPER_BIN="$DIRECT_BIN"
    echo "✓ Build successful! Binary at $WHISPER_BIN (deprecated; prefer build/bin/whisper-cli)"
else
    echo "✗ Build failed. Check for errors above."
    exit 1
fi

# Download whisper model if not present
if [ ! -f "./models/ggml-base.en.bin" ]; then
    echo "Downloading base.en model..."
    bash ./models/download-ggml-model.sh base.en
else
    echo "✓ Model already downloaded"
fi

cd ..

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Test whisper.cpp with:"
echo "  arecord -f cd -d 3 test.wav && $WHISPER_BIN -m ./whisper.cpp/models/ggml-base.en.bin -f test.wav"
echo ""
echo "Run the voice agent with:"
echo "  ./run.sh"
