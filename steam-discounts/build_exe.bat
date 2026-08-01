@echo off
REM ---------------------------------------------------------------------------
REM Build steam-discounts.exe locally on Windows.
REM Requires Python 3.7+ on PATH  (get it from https://www.python.org/downloads/,
REM tick "Add python.exe to PATH" in the installer).
REM Just double-click this file, or run it from a terminal.
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo [!] Python not found on PATH. Install Python 3.7+ from
  echo     https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^).
  pause
  exit /b 1
)

echo [1/2] Installing PyInstaller (one-time)...
python -m pip install --upgrade pyinstaller || goto :err

echo [2/2] Building steam-discounts.exe ...
python -m PyInstaller --onefile --clean --noconfirm ^
  --name steam-discounts ^
  --add-data "frontend;frontend" ^
  server.py || goto :err

echo.
echo Done.  Your exe is here:  %~dp0dist\steam-discounts.exe
echo Double-click it to launch the app (it opens your browser automatically).
pause
exit /b 0

:err
echo.
echo [!] Build failed. Make sure Python 3.7+ is installed and on PATH.
pause
exit /b 1
