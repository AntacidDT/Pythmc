@echo off
title Pythmc - Minecraft Clone
echo Starting Pythmc...
echo.
python run.py
if errorlevel 1 (
    echo.
    echo Python not found or error occurred.
    echo Make sure Python 3.8+ is installed.
    echo.
    pause
)
