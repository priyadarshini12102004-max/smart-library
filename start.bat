@echo off
echo Starting Smart Library System...
cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate

:: Start Flask app in a new terminal
start "" cmd /k "python app.py"

:: Wait 5 seconds for Flask to start
timeout /t 5 >nul

:: Start ngrok in a new terminal
start "" cmd /k "ngrok http 5000"

:: Optional: Wait a few seconds, then get ngrok URL and copy to clipboard
timeout /t 5 >nul
for /f "tokens=2" %%i in ('curl --silent http://127.0.0.1:4040/api/tunnels ^| findstr /i "public_url"') do (
    echo %%i | clip
)
echo Ngrok URL copied to clipboard!
pause
