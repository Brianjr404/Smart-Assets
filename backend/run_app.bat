:: filepath: e:\Late-Night\backend\venv\run_app.bat
@echo off
:: Activate the virtual environment
call venv\Scripts\activate

:: Start the Flask app in a new command prompt window
start cmd /k "python vinnie.py"


timeout /t 1 /nobreak > nul

:: Open the default web browser to the Flask app's URL
start http://127.0.0.1:5000

:: Keep the batch script window open
pause
