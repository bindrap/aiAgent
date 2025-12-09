@echo off
REM Test if current whisper.cpp supports CUDA

echo Testing whisper.cpp binary for CUDA support...
echo.

.\whisper-windows\Release\whisper-cli.exe --help 2>&1 | findstr /i "cuda gpu"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo CUDA support detected in current binary!
) else (
    echo.
    echo No CUDA support in current binary.
    echo You need to build whisper.cpp with CUDA enabled.
)

echo.
echo Current binary info:
.\whisper-windows\Release\whisper-cli.exe --version 2>&1

echo.
pause
