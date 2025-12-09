@echo off
REM Build whisper.cpp with CUDA support using CMake

echo Building whisper.cpp with CUDA support...
echo Prerequisites: CMake, Visual Studio Build Tools, CUDA Toolkit
echo.

set BUILD_DIR=whisper-cpp-cuda-build
set INSTALL_DIR=whisper-windows-cuda

REM Check if CMake is available
where cmake >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake not found. Please install CMake first.
    echo Download from: https://cmake.org/download/
    pause
    exit /b 1
)

REM Clone or use existing whisper.cpp
if not exist "%BUILD_DIR%" (
    echo Cloning whisper.cpp repository...
    git clone https://github.com/ggerganov/whisper.cpp.git %BUILD_DIR%
)

cd %BUILD_DIR%

REM Create build directory
if not exist "build" mkdir build
cd build

echo Configuring with CUDA support...
cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release

echo Building (this may take several minutes)...
cmake --build . --config Release

echo.
echo Build complete! Copying binaries...
cd ..\..

if not exist "%INSTALL_DIR%" mkdir %INSTALL_DIR%
xcopy /Y "%BUILD_DIR%\build\bin\Release\*.exe" "%INSTALL_DIR%\"
xcopy /Y "%BUILD_DIR%\build\bin\Release\*.dll" "%INSTALL_DIR%\"

echo.
echo CUDA-enabled whisper.cpp binaries are in: %INSTALL_DIR%
echo.
echo To use them, edit runWin.bat and change:
echo   --whisper-binary .\whisper-windows\Release\whisper-cli.exe
echo to:
echo   --whisper-binary .\whisper-windows-cuda\whisper-cli.exe
echo.
pause
