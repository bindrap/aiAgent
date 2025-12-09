@echo off
REM Build whisper.cpp with CUDA using Visual Studio environment

echo Searching for Visual Studio installation...

REM Try common Visual Studio paths
set VS_PATHS=^
"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" ^
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\Tools\VsDevCmd.bat" ^
"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\Tools\VsDevCmd.bat" ^
"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat" ^
"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\Common7\Tools\VsDevCmd.bat" ^
"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat"

set FOUND_VS=0
for %%P in (%VS_PATHS%) do (
    if exist %%P (
        echo Found Visual Studio at %%P
        call %%P
        set FOUND_VS=1
        goto :build
    )
)

:build
if %FOUND_VS%==0 (
    echo ERROR: Visual Studio not found!
    echo Please install Visual Studio Build Tools from:
    echo https://visualstudio.microsoft.com/downloads/
    echo.
    echo Or run this script from "Developer Command Prompt for VS"
    pause
    exit /b 1
)

echo Visual Studio environment loaded
echo.

set BUILD_DIR=whisper-cpp-cuda-build
set INSTALL_DIR=whisper-windows-cuda

cd %BUILD_DIR%

REM Create build directory
if not exist "build" mkdir build
cd build

echo Configuring with CUDA support using Visual Studio...
cmake .. -G "Visual Studio 17 2022" -A x64 -DGGML_CUDA=ON

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Trying with Visual Studio 16 2019...
    cmake .. -G "Visual Studio 16 2019" -A x64 -DGGML_CUDA=ON
)

echo Building (this may take several minutes)...
cmake --build . --config Release

cd ..\..

echo.
echo Copying binaries...
if not exist "%INSTALL_DIR%" mkdir %INSTALL_DIR%
xcopy /Y "%BUILD_DIR%\build\bin\Release\*.exe" "%INSTALL_DIR%\" 2>nul
xcopy /Y "%BUILD_DIR%\build\bin\Release\*.dll" "%INSTALL_DIR%\" 2>nul

REM Also check in different output location
xcopy /Y "%BUILD_DIR%\build\Release\*.exe" "%INSTALL_DIR%\" 2>nul
xcopy /Y "%BUILD_DIR%\build\Release\*.dll" "%INSTALL_DIR%\" 2>nul

if exist "%INSTALL_DIR%\whisper-cli.exe" (
    echo.
    echo SUCCESS! CUDA-enabled binaries installed to: %INSTALL_DIR%
    echo.
    echo To use GPU acceleration, edit runWin.bat and change:
    echo   --whisper-binary .\whisper-windows\Release\whisper-cli.exe
    echo to:
    echo   --whisper-binary .\whisper-windows-cuda\whisper-cli.exe
) else (
    echo.
    echo Build may have failed. Check the output above for errors.
)

echo.
pause
