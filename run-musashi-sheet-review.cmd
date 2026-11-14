@echo off
setlocal
cd /d "%~dp0"
set "BLENDER=%LOCALAPPDATA%\LegendaryBattleTools\blender-5.2.3-windows-x64\blender.exe"
if not exist "%BLENDER%" set "BLENDER=C:\Users\hun\Documents\BlenderPortable\blender-5.2.3-windows-x64\blender.exe"
if not exist "%BLENDER%" (echo Blender missing & pause & exit /b 1)
"%BLENDER%" --background --threads 6 --python "%~dp0tools\musashi_sheet_exterior_v3.py"
if errorlevel 1 (echo Rendering failed & pause & exit /b 1)
python "%~dp0tools\publish_musashi_sheet_v3.py"
if errorlevel 1 (echo Publishing failed & pause & exit /b 1)
start "" "%~dp0assets\characters\musashi\sheet_v3\musashi_exterior_preview.html"
echo Musashi review opened.
