import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import base64
import joblib
import secrets
from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODERS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'Encoders')

# List of all 47 Kenyan counties
KENYAN_COUNTIES = [
    'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet',
    'Embu', 'Garissa', 'Homa Bay', 'Isiolo', 'Kajiado',
    'Kakamega', 'Kericho', 'Kiambu', 'Kilifi', 'Kirinyaga',
    'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia',
    'Lamu', 'Machakos', 'Makueni', 'Mandera', 'Meru',
    'Migori', 'Marsabit', 'Mombasa', 'Murang\'a', 'Nairobi',
    'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua',
    'Nyeri', 'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River',
    'Tharaka-Nithi', 'Trans Nzoia', 'Turkana', 'Uasin Gishu',
    'Vihiga', 'Wajir', 'West Pokot'
]

# Property types
PROPERTY_TYPES = ['House', 'Apartment', 'Villa', 'Townhouse', 'Bungalow']

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                email TEXT,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP)''')
    # Login history table
    c.execute('''CREATE TABLE IF NOT EXISTS login_history
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN,
                FOREIGN KEY(user_id) REFERENCES users(id))''')
    # Property data table
    c.execute('''CREATE TABLE IF NOT EXISTS property_data
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                size_sqft REAL,
                location TEXT,
                property_type TEXT,
                price REAL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(added_by) REFERENCES users(id))''')
    # Create admin user if not exists
    admin_exists = c.execute('SELECT 1 FROM users WHERE username = "admin"').fetchone()
    if not admin_exists:
        admin_password = generate_password_hash("admin123")
        c.execute('INSERT INTO users (username, password, name, email, is_admin) VALUES (?, ?, ?, ?, ?)',
                 ('admin', admin_password, 'Admin User', 'admin@example.com', 1))
    conn.commit()
    conn.close()

# Initialize database and models
with app.app_context():
    init_db()
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

# Load the pre-trained model
try:
    model_path = os.path.join(ENCODERS_DIR, 'rf_model_compressed_lvl2.pkl')
    model = joblib.load(model_path)
    print("Compressed model loaded successfully.")
except Exception as e:
    print(f"Error loading compressed model: {e}")
    model = None

# Database helper functions
def get_db_connection():
    db_path = os.path.abspath('users.db')
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(name, email, username, password):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (name, email, username, password) VALUES (?, ?, ?, ?)',
                    (name, email, username, generate_password_hash(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def record_login(user_id, username, ip_address, user_agent, success=True):
    conn = get_db_connection()
    try:
        conn.execute('''INSERT INTO login_history 
                      (user_id, username, ip_address, user_agent, success) 
                      VALUES (?, ?, ?, ?, ?)''',
                   (user_id, username, ip_address, user_agent, success))
        if success and user_id:
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', 
                        (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Error recording login: {e}")
    finally:
        conn.close()

def predict_price(bedrooms, bathrooms, size_sqft, location, property_type='House'):
    try:
        # Load models and encoders using relative paths
        model_path = os.path.join(ENCODERS_DIR, 'rf_model_compressed_lvl2.pkl')
        location_encoder_path = os.path.join(ENCODERS_DIR, 'location_encoder.joblib')
        property_encoder_path = os.path.join(ENCODERS_DIR, 'property_encoder.joblib')
        
        model = joblib.load(model_path)
        le_location = joblib.load(location_encoder_path)
        le_property = joblib.load(property_encoder_path)

        # Validate inputs
        if location not in KENYAN_COUNTIES:
            raise ValueError(f"Invalid county: {location}")
        if property_type not in PROPERTY_TYPES:
            raise ValueError(f"Invalid property type: {property_type}")

        # Prepare input data
        input_data = pd.DataFrame({
            'bedrooms': [bedrooms],
            'bathrooms': [bathrooms],
            'size_sqft': [size_sqft],
            'location_encoded': [le_location.transform([location])[0]],
            'property_type_encoded': [le_property.transform([property_type])[0]]
        })

        # Predict the price
        return model.predict(input_data)[0]
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def home():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    if not user:
        flash('User not found')
        return redirect(url_for('logout'))
    return render_template('index.html', 
                           user=dict(user),
                           counties=KENYAN_COUNTIES,
                           property_types=PROPERTY_TYPES,
                           prediction_text="Your prediction will appear here.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Fetch user details by username
        user = get_user_by_username(username)

        # Prepare login details for recording
        login_details = {
            'user_id': user['id'] if user else None,
            'username': username,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }

        # Validate user credentials
        if user and check_password_hash(user['password'], password):
            # Successful login
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user.get('is_admin', False))

            # Record successful login
            record_login(**login_details, success=True)

            flash('Login successful!')
            return redirect(url_for('home'))

        # Record failed login attempt
        record_login(**login_details, success=False)
        flash('Invalid username or password')

    # Render the login form with enhanced flexibility
    return render_template(
        'login.html',
        auth_title="Login",
        form_action="/login",
        auth_action="Login",
        auth_switch_text="Don't have an account?",
        auth_switch_action="Sign Up",
        auth_switch_link="/signup",
        show_name=False,
        show_email=False,
        show_confirm=False
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if not all([name, email, username, password, confirm_password]):
            flash('All fields are required')
            return redirect(url_for('signup'))
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        if len(password) < 8:
            flash('Password must be at least 8 characters')
            return redirect(url_for('signup'))
        if create_user(name, email, username, password):
            flash('Account created successfully! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Username already exists')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        try:
            city_town = request.form.get('city_town', '').strip()
            bedrooms = int(request.form.get('bedrooms', 0))
            bathrooms = int(request.form.get('bathrooms', 0))
            lot_size_sqft = float(request.form.get('lot_size_sqft', 0))
            house_tax_rate = float(request.form.get('house_tax_rate', 0))
            year_built = int(request.form.get('year_built', 0))
            proximity_to_city = float(request.form.get('proximity_to_city', 0))
            predicted_price = predict_price(
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                size_sqft=lot_size_sqft,
                location=city_town,
                property_type='House'  # Default property type
            )
            formatted_price = f"KSh {predicted_price:,.2f}"
            return render_template('predict.html', prediction_text=f'Predicted House Price: {formatted_price}')
        except Exception as e:
            return render_template('predict.html', prediction_text=f'Error: {str(e)}')
    return render_template('predict.html')

@app.route('/ml/status')
@login_required
def ml_status():
    model_exists = os.path.exists('kenya_house_predictor.joblib')
    metrics = {}
    if model_exists and os.path.exists('model_metrics.json'):
        try:
            with open('model_metrics.json', 'r') as f:
                metrics = json.load(f)
        except:
            pass
    return render_template('model_status.html',
                         model_exists=model_exists,
                         metrics=metrics)

@app.route('/add-property', methods=['GET', 'POST'])
@login_required
def add_property():
    if request.method == 'POST':
        try:
            bedrooms = int(request.form.get('bedrooms', 0))
            bathrooms = int(request.form.get('bathrooms', 0))
            size_sqft = float(request.form.get('size_sqft', 0))
            location = request.form.get('location')
            property_type = request.form.get('property_type')
            price = float(request.form.get('price', 0))
            conn = get_db_connection()
            conn.execute('''INSERT INTO property_data 
                          (bedrooms, bathrooms, size_sqft, location, property_type, price, added_by)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (bedrooms, bathrooms, size_sqft, location, property_type, price, session['user_id']))
            conn.commit()
            conn.close()
            flash('Property data added successfully!')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error adding property: {str(e)}')
            return redirect(url_for('add_property'))
    return render_template('add_property.html', 
                       counties=KENYAN_COUNTIES,
                       property_types=PROPERTY_TYPES)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    # Run the app
    app.run(debug=True, use_reloader=False)