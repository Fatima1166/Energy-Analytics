@echo off
title Energy Analytics - launcher
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1"
echo.
echo Press any key to close this window (the services keep running).
pause >nul
