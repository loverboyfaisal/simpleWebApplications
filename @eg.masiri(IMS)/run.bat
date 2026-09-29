@echo off
rem masiriSystem launcher: run app.py with the project venv (env\Scripts)
rem the venv is not always portable between PCs (it records the original
rem python path in env\pyvenv.cfg), so fall back to system python + requirements.txt
rem once the server answers, the default browser opens http://localhost:9999 automatically

cd /d "%~dp0"

set PY=env\Scripts\python.exe

"%PY%" -c "import sys" >nul 2>&1
if %errorlevel%==0 (
    echo Starting masiriSystem with the project venv...
    call :launch "%PY%"
    goto end
)

echo Project venv is missing or broken on this PC.
echo Falling back to system python and installing requirements.txt...
python -m pip install -r requirements.txt
call :launch python

:launch
rem poll until the server answers, then open the browser (detached, no window)
start "" /b powershell -NoProfile -Command "for($i=0;$i -lt 60;$i++){try{Invoke-WebRequest -Uri 'http://127.0.0.1:9999/' -UseBasicParsing -TimeoutSec 1|Out-Null;$ok=$true;break}catch{Start-Sleep -Milliseconds 500}}; if($ok){Start-Process 'http://localhost:9999/'}"
echo.
echo Serving at http://localhost:9999/ (opens automatically once ready)
"%~1" app.py
goto :eof

:end
echo.
echo Server stopped. Press any key to close...
pause >nul
