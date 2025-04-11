:: filepath: e:\Late-Night\backend\venv\run_app.bat
@echo off
:: Activate the virtual environment
call venv\Scripts\activate
:: Start the Flask app
start http://127.0.0.1:5000
python vinnie.py
pause