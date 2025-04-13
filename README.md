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

- Python 3.x
- Git
- Git LFS (for handling large model files)

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Brianjr404/Smart-Assets.git
   cd Smart-Assets
   ```

2. Install Git LFS and pull the model files:
   ```bash
   git lfs install
   git lfs pull
   ```

3. Navigate to the backend directory:
   ```bash
   cd backend
   ```

4. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Windows
1. Double-click `run_app.bat` in the backend directory
2. Or run from command line:
   ```bash
   python vinnie.py
   ```

### Linux/Mac
```bash
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