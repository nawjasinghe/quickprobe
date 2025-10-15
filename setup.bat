@echo off
REM setup script - creates virtual environment and installs dependencies

echo Setting up PingSLO environment...
echo.

REM check if python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM create virtual environment if it doesnt exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM install dependencies
echo.
echo Installing dependencies...
pip install numpy pyyaml aiohttp pytest

echo.
echo Setup complete!
echo.
echo To run the tool:
echo   run.bat run --targets urls.txt
echo   run.bat sample --url google.com
echo.
echo To run tests:
echo   test.bat
echo.
pause
