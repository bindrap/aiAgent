# Terminal Voice AI Agent

A local-first voice assistant for the terminal using **whisper.cpp** for speech recognition and **Ollama** for AI text generation. Works on both Windows and Linux/macOS with GPU acceleration support!

![Language](https://img.shields.io/badge/python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 🎤 **Voice Input**: Record audio with simple keyboard controls
- ⌨️ **Text Input**: Type messages directly when you don't want to use voice
- 🤖 **Local AI**: Runs entirely on your machine - no cloud services
- 🚀 **GPU Accelerated**: Supports CUDA for both whisper.cpp and Ollama
- 🎨 **Styled Output**: Beautiful colored terminal UI with formatted responses
- 💬 **Conversation Memory**: Maintains context across multiple turns
- ⚡ **Fast**: Optimized for quick transcription and response generation
- 🔒 **Private**: All processing happens locally

## Demo

```
Voice agent ready.
Press Ctrl+T to start/stop recording. Press Ctrl+R to type a message. Press q to quit.

[Type your message, press Enter to send]
> What did Einstein discover?

╭─ YOU ────────────────────────────────────────────────────────╮
│ What did Einstein discover?                                  │
╰──────────────────────────────────────────────────────────────╯

╭─ ASSISTANT ──────────────────────────────────────────────────╮
│ Albert Einstein made several groundbreaking discoveries:     │
│                                                               │
│ 1. Special Relativity (1905) - E=mc²                        │
│ 2. General Relativity (1915) - Gravity as spacetime         │
│    curvature                                                  │
│ 3. Photoelectric Effect - Won him the Nobel Prize           │
╰──────────────────────────────────────────────────────────────╯
```

## Prerequisites

- **Python 3.9+** with pip
- **Microphone** that works with your system
- **Ollama** - [Download here](https://ollama.com/download)
- **whisper.cpp** binaries (instructions below)
- **CUDA Toolkit** (optional, for GPU acceleration)

## Quick Start

### Windows

1. **Install Ollama**
   ```powershell
   # Download and install from https://ollama.com/download/windows
   ollama pull llama3.1:8B
   ```

2. **Clone and Setup**
   ```powershell
   git clone https://github.com/bindrap/aiAgent.git
   cd aiAgent
   python -m venv windowsvenv
   .\windowsvenv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Download whisper.cpp**
   - Get pre-built Windows binaries from [whisper.cpp releases](https://github.com/ggerganov/whisper.cpp/releases)
   - Extract to `whisper-windows/Release/`
   - Or run `.\download-better-model.bat` to download a better model

4. **Run**
   ```powershell
   .\runWin.bat
   ```

### Linux/macOS

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3
   ```

2. **Clone and Setup**
   ```bash
   git clone https://github.com/bindrap/aiAgent.git
   cd aiAgent
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Build whisper.cpp**
   ```bash
   git clone https://github.com/ggerganov/whisper.cpp.git
   cd whisper.cpp
   make
   bash ./models/download-ggml-model.sh base.en
   cd ..
   ```

4. **Run**
   ```bash
   python -m voice \
     --model llama3 \
     --whisper-binary ./whisper.cpp/main \
     --whisper-model ./whisper.cpp/models/ggml-base.en.bin
   ```

## Controls

- **Ctrl+T** - Start/Stop voice recording and send to AI
- **Ctrl+R** - Type a text message and send to AI (no voice needed)
- **q** - Quit the application

## Configuration

### Models

**Whisper Models** (accuracy vs speed):
- `ggml-tiny.en.bin` - Fastest, least accurate
- `ggml-base.en.bin` - Good balance (default)
- `ggml-small.en.bin` - Better accuracy, slower
- `ggml-medium.en.bin` - Best accuracy, slowest

**Ollama Models**:
- `llama3.1:8B` - Recommended for quality
- `qwen2.5:1.5b` - Faster, smaller model
- Any model from [Ollama library](https://ollama.com/library)

### Command-line Flags

```bash
--model              # Ollama model name (default: llama3)
--whisper-binary     # Path to whisper.cpp binary
--whisper-model      # Path to whisper.cpp model file
--language           # Language code (default: en)
--sample-rate        # Audio sample rate (default: 16000)
--threads            # Whisper threads (default: 4)
--max-history        # Conversation turns to keep (default: 10)
--keep-recordings    # Don't delete audio files after transcription
--system             # Custom system prompt
```

## GPU Acceleration

### Whisper.cpp with CUDA

Your whisper.cpp binary automatically uses GPU if available. To verify:
```powershell
.\test-whisper-cuda.bat
```

To build with CUDA support:
```powershell
.\build-whisper-cuda-vs.bat
```

### Ollama with GPU

Ollama automatically detects and uses your GPU. Check the startup logs to verify GPU acceleration is active.

## Project Structure

```
aiAgent/
├── voice/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── main.py              # Main application logic
│   ├── audio.py             # Audio recording
│   ├── whisper_client.py    # Whisper.cpp wrapper
│   └── ollama_client.py     # Ollama API client
├── requirements.txt         # Python dependencies
├── runWin.bat              # Windows launcher
├── CLAUDE.md               # Project goals & design
└── README.md               # This file
```

## Troubleshooting

**Colors not showing on Windows?**
- Make sure colorama is installed: `pip install colorama`
- Use Windows Terminal or PowerShell 7+

**Ollama CUDA errors?**
- Restart Ollama: `taskkill /IM ollama.exe /F` then restart
- Try a smaller model
- Set `OLLAMA_NO_GPU=1` to use CPU

**Transcription inaccurate?**
- Use a larger whisper model (`ggml-small.en.bin` or `ggml-medium.en.bin`)
- Speak clearly and reduce background noise
- Adjust `--sample-rate` if needed

**Microphone not working?**
- List devices: `python -c "import sounddevice as sd; print(sd.query_devices())"`
- Specify device: `--input-device <device_id>`

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Fast whisper inference
- [Ollama](https://ollama.com) - Local LLM runtime
- Built with guidance from Claude (Anthropic)
