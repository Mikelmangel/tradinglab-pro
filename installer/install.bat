@echo off
title TradingLab Pro — Instalador
color 0B
echo.
echo  TradingLab Pro v2.0 — Instalador Windows
echo.
python --version >nul 2>&1 || (echo ERROR: Python no encontrado. & pause & exit /b 1)
cd /d "%~dp0.."
python installer\install.py
pause
