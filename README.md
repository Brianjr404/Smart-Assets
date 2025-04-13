# Property Price Prediction System

A machine learning-based system for predicting property prices with a user-friendly web interface.

## Project Structure

```
.
├── backend/              # Backend application code
│   ├── venv/            # Python virtual environment
│   ├── vinnie.py        # Main application file
│   ├── compress_model.py # Model compression utilities
│   ├── requirements.txt # Python dependencies
│   ├── run_app.bat      # Windows startup script
│   ├── templates/       # HTML templates
│   └── static/          # Static assets (CSS, JS, images)
├── Encoders/            # Trained models and encoders
│   ├── rf_model_compressed_lvl2.pkl
│   ├── location_encoder.joblib
│   └── property_encoder.joblib
├── templates/           # Frontend templates
├── static/             # Frontend static assets
└── pyrightconfig.json  # Type checking configuration
```

## Prerequisites

### Required Software

1. **Git** - Version control system
   - Windows: Download from https://git-scm.com/download/win
   - Linux: `sudo apt install git` (Ubuntu/Debian) or `sudo dnf install git` (Fedora)
   - Mac: `xcode-select --install` or download from https://git-scm.com/download/mac
   - Verify installation: `git --version`

2. **Git LFS** - For handling large model files
   - Windows: Download from https://git-lfs.github.com/
   - Linux: 
     ```bash
     # Ubuntu/Debian
     curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
     sudo apt-get install git-lfs
     
     # Fedora
     curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash
     sudo dnf install git-lfs
     ```
   - Mac: `brew install git-lfs` or download from https://git-lfs.github.com/
   - Verify installation: `git lfs install`

3. **Python 3.x** - Programming language
   - Windows: Download from https://www.python.org/downloads/
   - Linux: `sudo apt install python3 python3-pip` (Ubuntu/Debian) or `sudo dnf install python3 python3-pip` (Fedora)
   - Mac: Download from https://www.python.org/downloads/macos/ or `brew install python`
   - Verify installation: `python --version` or `python3 --version`

### Verification Steps

After installing all prerequisites, verify your setup:

1. Open Command Prompt/PowerShell (Windows) or Terminal (Linux/Mac)
2. Run these commands to verify installations:
   ```bash
   git --version
   git lfs install
   python --version  # or python3 --version
   ```

If any command is not recognized, please reinstall the corresponding software.

## Using the Command Line

### Windows
1. Open Command Prompt or PowerShell:
   - Press `Windows + R`
   - Type `cmd` or `powershell`
   - Press Enter

2. Navigate to your desired directory:
   ```bash
   cd path\to\desired\directory
   ```

### Linux/Mac
1. Open Terminal:
   - Press `Ctrl + Alt + T` (Linux)
   - Open Spotlight (`Cmd + Space`) and type "Terminal" (Mac)

2. Navigate to your desired directory:
   ```bash
   cd /path/to/desired/directory
   ```

## Setup Instructions

1. Clone the repository:
   ```bash
   # Open your command line tool (Command Prompt/PowerShell/Terminal)
   # Navigate to where you want to store the project
   git clone https://github.com/Brianjr404/Smart-Assets.git
   cd Smart-Assets
   ```

2. Install Git LFS and pull the model files:
   ```bash
   # In the same command line window
   git lfs install
   git lfs pull
   ```

3. Navigate to the backend directory:
   ```bash
   # Still in the same command line window
   cd backend
   ```

4. Create and activate a virtual environment:
   ```bash
   # Windows (Command Prompt/PowerShell)
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac (Terminal)
   python3 -m venv venv
   source venv/bin/activate
   ```

5. Install dependencies:
   ```bash
   # Make sure you see (venv) at the start of your command line
   pip install -r requirements.txt
   ```

## Running the Application

### Windows
1. Using Command Prompt/PowerShell:
   ```bash
   # Make sure you're in the backend directory and virtual environment is activated
   # You should see (venv) at the start of your command line
   python vinnie.py
   ```

2. Or simply double-click `run_app.bat` in the backend directory

### Linux/Mac
```bash
# Open Terminal
# Navigate to the backend directory
# Activate virtual environment
# Run the application
python vinnie.py
```

The application will be available at: http://127.0.0.1:5000

## Accessing the Application

1. Open your web browser and go to: http://127.0.0.1:5000
2. Default admin credentials:
   - Username: admin
   - Password: admin123

## Features

- User authentication (signup/login)
- Property price prediction
- Property data management
- Admin dashboard
- Machine learning model integration

## Database

The application uses SQLite for data storage. The database file is located at:
- `backend/users.db`

Tables:
- `users`: Stores user information
- `login_history`: Tracks login attempts
- `property_data`: Stores property information
- `predictions`: Stores prediction results

## Troubleshooting

1. If models fail to load:
   - Ensure Git LFS is installed
   - Run `git lfs pull` to download model files
   - Check if model files exist in the Encoders directory

2. If database errors occur:
   - Delete the existing database file
   - Restart the application (it will create a new database)

3. If virtual environment issues:
   - Delete the venv directory
   - Follow setup instructions again

4. If command not found errors:
   - Make sure you're in the correct directory
   - Check if Python and Git are properly installed
   - Verify that the virtual environment is activated (you should see (venv) at the start of your command line)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Contact

[Add your contact information here] 