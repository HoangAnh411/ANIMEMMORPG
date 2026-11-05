@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\U01\StopGNetwork.ps1"
if errorlevel 1 pause
