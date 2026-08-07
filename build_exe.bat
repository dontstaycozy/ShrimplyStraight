@echo off
title ShrimplyStraight - Standalone EXE Builder
echo =========================================================
echo       ShrimplyStraight - Standalone EXE Builder
echo =========================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found on your system!
    echo Please install Python 3.9 - 3.12 and add it to your PATH.
    echo.
    pause
    exit /b
)

echo [1/3] Checking and installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [2/3] Building standalone executable with PyInstaller...
echo This might take a minute, please wait...
echo.

python -m PyInstaller --noconsole --onedir ^
    --distpath ".\dist" ^
    --workpath ".\build" ^
    --name "ShrimplyStraight" ^
    --icon="assets/images/shrimp_icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import "popups" ^
    --hidden-import "popups.popup_manager" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    --noconfirm ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check the output above for errors.
    pause
    exit /b
)

echo.
echo [3/3] Ensuring assets folder exists in dist for easy user customization...
if not exist "dist\ShrimplyStraight\assets" (
    xcopy /E /I /Y "assets" "dist\ShrimplyStraight\assets" >nul
)

echo.
echo =========================================================
echo                     BUILD SUCCESSFUL!
echo =========================================================
echo.
echo Your standalone application folder is ready at:
echo    dist\ShrimplyStraight\
echo.
echo To share with your friend:
echo  1. Zip the entire "dist\ShrimplyStraight" folder.
echo  2. Send them the zip file.
echo  3. They simply extract and double-click "ShrimplyStraight.exe"!
echo     (No Python installation needed on their machine!)
echo =========================================================
echo.
pause
