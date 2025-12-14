# Setup Guide for Arch Linux with AMD GPU (7800XT)

This guide walks through setting up the Terminal Voice AI Agent on Arch Linux with ROCm support for your AMD 7800XT GPU.

## Prerequisites

### 1. Install System Packages

```bash
# Update system
sudo pacman -Syu

# Install Python and development tools
sudo pacman -S python python-pip base-devel git cmake

# Install ROCm for AMD GPU support
sudo pacman -S rocm-hip-sdk rocm-opencl-sdk

# Install audio libraries
sudo pacman -S portaudio alsa-utils

# Install optional: for better microphone support
sudo pacman -S pulseaudio pulseaudio-alsa
```

### 2. Verify ROCm Installation

```bash
# Check if ROCm can see your GPU
rocminfo | grep -A 5 "Name:"

# You should see your AMD 7800XT listed
```

## Setup Steps

### Step 1: Install Ollama with ROCm Support

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify Ollama is using ROCm (it auto-detects AMD GPUs)
ollama --version

# Pull a model (start with a smaller one for testing)
ollama pull llama3.1:8b

# Optional: pull a faster, smaller model
ollama pull qwen2.5:1.5b
```

**Verify GPU usage:**
```bash
# In another terminal, watch GPU usage
watch -n 1 rocm-smi

# Then run a test
ollama run llama3.1:8b "Hello, how are you?"
```

### Step 2: Set Up Python Environment

```bash
cd /home/parteek/Documents/aiAgent

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Build whisper.cpp with ROCm Support

```bash
cd /home/parteek/Documents/aiAgent

# Clone whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp

# Build with ROCm/HIP support for AMD GPU
make GGML_HIPBLAS=1

# Download a whisper model (base.en is a good balance)
bash ./models/download-ggml-model.sh base.en

# Optional: download a better model
# bash ./models/download-ggml-model.sh small.en

# Test whisper.cpp
./build/bin/whisper-cli --help

cd ..
```

**Test GPU acceleration:**
```bash
# Record a test audio (speak for a few seconds)
arecord -f cd -d 5 test.wav

# Transcribe with GPU
./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-base.en.bin -f test.wav

# You should see CUDA/GPU initialization messages
```

### Step 4: Configure Audio Input

```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test recording (optional)
python -c "
import sounddevice as sd
import soundfile as sf
duration = 3
print('Recording for 3 seconds...')
audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1)
sd.wait()
sf.write('test_recording.wav', audio, 16000)
print('Saved to test_recording.wav')
"
```

If you see permission errors, add your user to the audio group:
```bash
sudo usermod -aG audio $USER
# Log out and back in for this to take effect
```

## Running the Agent

### Basic Usage

```bash
cd /home/parteek/Documents/aiAgent
source venv/bin/activate

python -m voice \
  --model llama3.1:8b \
  --whisper-binary ./whisper.cpp/build/bin/whisper-cli \
  --whisper-model ./whisper.cpp/models/ggml-base.en.bin
```

### Recommended Configuration

```bash
python -m voice \
  --model llama3.1:8b \
  --whisper-binary ./whisper.cpp/build/bin/whisper-cli \
  --whisper-model ./whisper.cpp/models/ggml-base.en.bin \
  --threads 8 \
  --system "You are a helpful AI assistant. Be concise and clear."
```

### Create a Launch Script

```bash
cat > run.sh << 'EOF'
#!/bin/bash
cd /home/parteek/Documents/aiAgent
source venv/bin/activate
python -m voice \
  --model llama3.1:8b \
  --whisper-binary ./whisper.cpp/build/bin/whisper-cli \
  --whisper-model ./whisper.cpp/models/ggml-base.en.bin \
  --threads 8 \
  --system "You are a helpful AI assistant. Be concise and clear."
EOF

chmod +x run.sh

# Now you can run with:
./run.sh
```

## Controls

- **Ctrl+T** - Start/Stop voice recording and send to AI
- **Ctrl+R** - Type a text message (no voice needed)
- **q** - Quit the application

## GPU Monitoring

Monitor your AMD GPU while using the agent:

```bash
# Terminal 1: Watch GPU usage
watch -n 1 rocm-smi

# Terminal 2: Run the voice agent
./run.sh
```

## Troubleshooting

### Ollama Not Using GPU

```bash
# Check Ollama logs
journalctl -u ollama -f

# Force Ollama to restart
sudo systemctl restart ollama

# Verify ROCm is available
rocminfo
```

### Audio Issues

```bash
# Test microphone
arecord -f cd -d 3 test.wav && aplay test.wav

# List devices
arecord -l

# If using PulseAudio, check it's running
pulseaudio --check -v
```

### Whisper.cpp Not Using GPU

Make sure you built with `GGML_HIPBLAS=1`:
```bash
cd whisper.cpp
make clean
make GGML_HIPBLAS=1
```

### Permission Denied Errors

```bash
# Add user to audio group
sudo usermod -aG audio $USER

# Add user to video group for GPU access
sudo usermod -aG video $USER
sudo usermod -aG render $USER

# Log out and back in
```

## Performance Optimization

### For AMD 7800XT

```bash
# Set ROCm visible devices (if you have multiple GPUs)
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Increase threads for your CPU
python -m voice --threads 16 ...  # Adjust based on your CPU cores
```

### Model Recommendations

**For best quality:**
- Whisper: `ggml-small.en.bin` or `ggml-medium.en.bin`
- Ollama: `llama3.1:8b`

**For best speed:**
- Whisper: `ggml-tiny.en.bin` or `ggml-base.en.bin`
- Ollama: `qwen2.5:1.5b`

## Next Steps

1. Test the basic setup with Ctrl+R (text input) first
2. Once working, test Ctrl+T (voice input)
3. Experiment with different models
4. Monitor GPU usage to ensure acceleration is working

Enjoy your GPU-accelerated voice AI agent!
