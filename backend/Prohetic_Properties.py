import webbrowser
from threading import Timer
from vinnie import app  # Import the Flask app from vinnie.py

# Function to open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Start a timer to open the browser after the server starts
    Timer(1, open_browser).start()
    # Run the Flask app
    app.run(debug=True)