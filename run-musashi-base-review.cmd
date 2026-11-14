@echo off
setlocal
cd /d "%~dp0"
set "BLENDER=%LOCALAPPDATA%\LegendaryBattleTools\blender-5.2.3-windows-x64\blender.exe"
if not exist "%BLENDER%" set "BLENDER=C:\Users\hun\Documents\BlenderPortable\blender-5.2.3-windows-x64\blender.exe"
if not exist "%BLENDER%" (echo Blender executable not found & pause & exit /b 1)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\download_musashi_cc0_base.ps1"
if errorlevel 1 (echo Source download failed & pause & exit /b 1)
"%BLENDER%" --background --threads 6 --python "%~dp0tools\build_musashi_realistic_base.py"
if errorlevel 1 (echo Rebuild failed & pause & exit /b 1)
start "" "%~dp0assets\characters\musashi\rebuild_v1\musashi_anatomy_base_preview.html"
