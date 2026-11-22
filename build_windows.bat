@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher ^(py^) is not installed.
    echo Please install Python 3.12 and select the option to add it to PATH.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo Python 3.12 is required. Install it from python.org.
        pause
        exit /b 1
    )
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\download_vazirmatn.ps1"
if errorlevel 1 (
    echo Vazirmatn is required. Check the font download and try again.
    pause
    exit /b 1
)
set QT_QPA_PLATFORM=offscreen
python -c "from PyQt6.QtWidgets import QApplication; from html_tooldesk.theme import install_font; a=QApplication([]); f=install_font(a); assert 'Vazirmatn' in f, 'Font not loaded'"
if errorlevel 1 exit /b 1
set QT_QPA_PLATFORM=
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
python -m PyInstaller --clean --noconfirm HTMLToolDesk.spec
if errorlevel 1 (
    echo Failed to build the EXE. See logs above.
    pause
    exit /b 1
)
echo.
echo EXE created: %CD%\dist\HTMLToolDesk\HTMLToolDesk.exe
echo IMPORTANT: Keep the whole HTMLToolDesk folder together.
pause
endlocal