@echo off
echo [*] Building Cute Little Trader...

:: Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PyInstaller not found. Installing...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [X] Failed to install PyInstaller
        exit /b 1
    )
)

echo [*] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [X] Failed to install dependencies
    exit /b 1
)

echo [*] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [*] Building executable...
python -m PyInstaller --clean bot.spec

if %errorlevel% equ 0 (
    echo [+] Build successful!
    echo [*] Executable is in: dist\cute-little-trader.exe
) else (
    echo [X] Build failed
    exit /b 1
)

pause 