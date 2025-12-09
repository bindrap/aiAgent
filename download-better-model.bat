@echo off
REM Download a more accurate whisper model

echo Downloading ggml-small.en model for better accuracy...
echo This will take a few minutes...

curl -L "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin" -o ".\whisper.cpp\models\ggml-small.en.bin"

echo.
echo Download complete!
echo To use this model, edit runWin.bat and change:
echo   --whisper-model .\whisper.cpp\models\ggml-base.en.bin
echo to:
echo   --whisper-model .\whisper.cpp\models\ggml-small.en.bin
echo.
pause
