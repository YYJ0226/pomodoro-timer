@echo off
chcp 65001 >nul
title 番茄钟
cd /d "%~dp0"
python pomodoro.py
pause