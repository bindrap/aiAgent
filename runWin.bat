@echo off
REM Voice Agent Runner for Windows
REM Activates virtual environment and starts the voice agent

echo Activating virtual environment...
call .\windowsvenv\Scripts\activate.bat

echo Starting voice agent...
python -m voice ^
  --model llama3.1:8B ^
  --whisper-binary .\whisper-windows\Release\whisper-cli.exe ^
  --whisper-model .\whisper.cpp\models\ggml-small.en.bin ^
  --language en ^
  --sample-rate 16000

pause
