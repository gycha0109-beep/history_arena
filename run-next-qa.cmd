@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER if exist "%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe" set "BLENDER=%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe"
if not defined BLENDER for /f "delims=" %%B in ('where blender 2^>nul') do if not defined BLENDER set "BLENDER=%%B"
if not defined BLENDER (
  echo Blender 5.2 not found. Install Blender 5.2 or set BLENDER_EXE to its blender.exe.
  exit /b 1
)
where python >nul 2>nul || (echo Python 3 is required & exit /b 1)
where ffmpeg >nul 2>nul || (echo FFmpeg is required & exit /b 1)
if not exist "samples\external\kinemiq_dual_guard_idle.glb" (
  echo Missing rig asset. Run git lfs pull in this directory.
  exit /b 1
)
if not exist "samples\external\qa_katana_rigid.glb" (
  echo Missing katana. Run git lfs pull.
  exit /b 1
)
if not exist "samples\external\qa_wakizashi_rigid.glb" (
  echo Missing wakizashi. Run git lfs pull.
  exit /b 1
)
if not exist "captures\qa\right_grip\right_katana_grip_analysis.json" (
  "%BLENDER%" --background --python tools\right_grip_qa.py
  if errorlevel 1 exit /b 1
)
if not exist "captures\qa\left_grip\left_wakizashi_grip_analysis.json" (
  "%BLENDER%" --background --python tools\left_grip_qa.py
  if errorlevel 1 exit /b 1
)
echo [1/4] Render dual-sword V5 and original-hand closeups
"%BLENDER%" --background --python tools\dual_grip_guard_v5.py
if errorlevel 1 exit /b 1
echo [2/4] Verify blade orientation and left index penetration
"%BLENDER%" --background --python tools\audit_guard_v5.py
if errorlevel 1 exit /b 1
echo [3/4] Create vertical five-second MP4
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i tools\dual_guard_v5_angles.ffconcat -vf fps=60 -t 5 -r 60 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart captures\qa\dual_grip_guard_v5\dual_guard_angles_5s.mp4
if errorlevel 1 exit /b 1
copy /y tools\dual_guard_v5_viewer.html captures\qa\dual_grip_guard_v5\dual_grip_guard_preview.html >nul
if errorlevel 1 exit /b 1
echo [4/4] Check HTML media and output metadata
python tools\validate_guard_v5.py
if errorlevel 1 exit /b 1
del /q captures\qa\dual_grip_guard_v5\*.blend1 2>nul
echo READY: %CD%\captures\qa\dual_grip_guard_v5\dual_grip_guard_preview.html
start "" "%CD%\captures\qa\dual_grip_guard_v5\dual_grip_guard_preview.html"
exit /b 0
