@echo off
REM Lupine Engine Build Script
REM Run this to compile the engine into a standalone executable

echo ========================================
echo Lupine Engine Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script from the Lupine Engine root directory
    pause
    exit /b 1
)

echo Starting engine compilation...
echo.

REM Run the Python compiler script
python build_engine.py %*

REM Check if compilation was successful
if errorlevel 1 (
    echo.
    echo ========================================
    echo BUILD FAILED
    echo ========================================
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL
    echo ========================================
    echo The compiled engine is ready in the dist folder
    echo.
    pause
)
