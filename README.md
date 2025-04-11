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

## Features

- Property price prediction using machine learning
- User-friendly web interface
- Model compression for efficient deployment
- Location and property type encoding

## Setup Instructions

1. Clone the repository
2. Navigate to the backend directory:
   ```bash
   cd backend
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application:
   - Windows: Double-click `run_app.bat`
   - Or from command line: `python vinnie.py`

## Dependencies

- Python 3.x
- Flask
- scikit-learn
- pandas
- numpy
- joblib

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