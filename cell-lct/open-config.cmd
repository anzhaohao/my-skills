@echo off
rem Cell-lct config page launcher.
rem Starts the local server (127.0.0.1) and opens the browser automatically.
rem Close this window or press Ctrl+C to stop the server.
setlocal

set "SERVER=%~dp0config-ui\server.py"
if not exist "%SERVER%" set "SERVER=%~dp0..\config-ui\server.py"
if not exist "%SERVER%" (
  echo [ERROR] config-ui\server.py was not found next to this script.
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  if "%CELL_LCT_UI_NO_BROWSER%"=="1" (
    py -3 "%SERVER%"
  ) else (
    py -3 "%SERVER%" --open-browser
  )
  goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
  if "%CELL_LCT_UI_NO_BROWSER%"=="1" (
    python "%SERVER%"
  ) else (
    python "%SERVER%" --open-browser
  )
  goto :done
)

echo [ERROR] Python 3 is required to open the Cell-lct config page.
pause
exit /b 1

:done
if errorlevel 1 (
  echo [ERROR] The config server exited with code %errorlevel%.
  pause
)
endlocal
