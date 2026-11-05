@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\U01\PlayG.ps1" %*
if errorlevel 1 pause
