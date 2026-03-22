@echo off
title Macro Portfolio Analyzer - Run Analysis

echo Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Please run install_and_run.bat first to install dependencies.
    pause
    exit /b 1
)

echo.
echo Running portfolio analysis...
".venv\Scripts\python.exe" analyze_portfolio.py

echo.
echo Analysis finished.
pause
