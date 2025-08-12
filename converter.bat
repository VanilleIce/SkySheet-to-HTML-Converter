:: Copyright (C) 2025 VanilleIce
@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo ==============================================
echo  SkySheet to HTML Converter
echo ==============================================
echo.

:: Check for input file
if "%~1"=="" (
    echo ERROR: No file specified!
    echo.
    echo USAGE:
    echo   1. Drag file onto this batch/exe file
    echo.
    echo CUSTOM LAYOUT:
    echo   Place custom.xml next to converter.bat
    echo   with your keyboard layout definition
    echo.
    pause
    exit /b 1
)

:: Set script path
set PY_SCRIPT=%~dp0converter.py

:: Verify Python script exists
if not exist "%PY_SCRIPT%" (
    echo.
    echo ERROR: converter.py not found
    echo Ensure it's in the same folder
    echo.
    pause
    exit /b 1
)

:: Run conversion
echo.
echo Converting "%~nx1"...
python "%PY_SCRIPT%" "%~1"

:: Handle result
if errorlevel 1 (
    echo.
    echo CONVERSION FAILED!
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo CONVERSION SUCCESSFUL!
    echo HTML file created in same folder
    echo.
    timeout /t 3 > nul
    exit /b 0
)