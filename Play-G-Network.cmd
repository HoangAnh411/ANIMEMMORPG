@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\U01\ReviewGNetwork.ps1" %*
if errorlevel 1 pause
