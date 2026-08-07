@echo off
title ShrimplyStraight - Setup & Installation
echo =========================================================
echo       🦐 ShrimplyStraight - One-Click Installer
echo =========================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not currently installed or not in your PATH.
    echo.
    echo Trying to install Python automatically via winget...
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Could not auto-install Python.
        echo Please download and install Python from: https://www.python.org/downloads/
        echo (Make sure to check "Add Python to PATH" during installation!)
        pause
        exit /b
    )
)

echo [1/3] Creating isolated virtual environment (venv)...
if not exist "venv" (
    python -m venv venv
)

echo.
echo [2/3] Installing required packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo [3/3] Creating Desktop Shortcut...
set "SCRIPT_DIR=%~dp0"
set "VBS_PATH=%SCRIPT_DIR%Start_Shrimply.vbs"
set "ICON_PATH=%SCRIPT_DIR%assets\images\shrimp_icon.ico"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Shrimply Straight.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = '%ICON_PATH%'; $s.Save()"

echo.
echo =========================================================
echo               🦐 SETUP COMPLETE! 🦐
echo =========================================================
echo.
echo A "Shrimply Straight" shortcut has been added to your Desktop!
echo Double-click it anytime to start posture monitoring.
echo.
pause
