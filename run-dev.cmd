@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-dev.ps1" %*
set RESULT=%ERRORLEVEL%
if not "%RESULT%"=="0" (
  echo.
  echo [ERROR] 실행에 실패했습니다. 위 메시지를 확인하세요.
  pause
)
exit /b %RESULT%
