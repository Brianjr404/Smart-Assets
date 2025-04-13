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
app.config['SESSION_TYPE'] = 'filesystem'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    db_path = os.path.join(BASE_DIR, 'users.db')
    print(f"Initializing database at: {db_path}")  # Debug print
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Enable foreign key constraints
    c.execute('PRAGMA foreign_keys = ON')
    
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
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''')
    
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
                FOREIGN KEY(added_by) REFERENCES users(id) ON DELETE CASCADE)''')
    
    # Predictions table
    c.execute('''CREATE TABLE IF NOT EXISTS predictions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                location TEXT,
                property_type TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                size_sqft REAL,
                predicted_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''')
    
    # Create admin user if not exists
    admin_exists = c.execute('SELECT 1 FROM users WHERE username = "admin"').fetchone()
    if not admin_exists:
        admin_password = generate_password_hash("admin123")
        c.execute('INSERT INTO users (username, password, name, email, is_admin) VALUES (?, ?, ?, ?, ?)',
                 ('admin', admin_password, 'Admin User', 'admin@example.com', 1))
    
    conn.commit()
    conn.close()
    print("Database initialization complete")  # Debug print

# Database helper functions
def get_db_connection():
    db_path = os.path.join(BASE_DIR, 'users.db')
    print(f"Connecting to database at: {db_path}")  # Debug print
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(name, email, username, password):
    conn = get_db_connection()
    try:
        # Check if username already exists
        existing_user = conn.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            print(f"Username {username} already exists")  # Debug print
            return False
            
        # Insert new user
        conn.execute('INSERT INTO users (name, email, username, password) VALUES (?, ?, ?, ?)',
                    (name, email, username, generate_password_hash(password)))
        conn.commit()
        print(f"User {username} created successfully")  # Debug print
        return True
    except sqlite3.Error as e:
        print(f"Database error in create_user: {e}")  # Debug print
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
        print(f"Login recorded for user {username}")  # Debug print
    except Exception as e:
        print(f"Error recording login: {e}")  # Debug print
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
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        
        if not user:
            flash('User not found. Please login again.', 'error')
            return redirect(url_for('logout'))
            
        # Convert user to dict for template
        user_dict = dict(user)
        
        # Add welcome message for first-time login
        if not user_dict.get('last_login'):
            flash('Welcome to Smart Assets! We\'re glad to have you here.', 'success')
        else:
            flash('Welcome back!', 'success')
            
        return render_template('index.html', user=user_dict)
    except Exception as e:
        flash('An error occurred while loading your dashboard. Please try again.', 'error')
        return redirect(url_for('logout'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('login'))

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

            flash('Login successful! Welcome back!', 'success')
            return redirect(url_for('home'))

        # Record failed login attempt
        record_login(**login_details, success=False)
        flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html',
                         form_action=url_for('login'),
                         auth_title="Login",
                         auth_action="Login",
                         auth_switch_text="Don't have an account?",
                         auth_switch_action="Sign Up",
                         auth_switch_link=url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate all fields
        if not all([name, email, username, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('signup'))
        
        # Validate email format
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('signup'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('signup'))
            
        if create_user(name, email, username, password):
            flash('Account created successfully! Please login to continue.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists. Please choose another one.', 'error')
    
    return render_template('signup.html',
                         form_action=url_for('signup'),
                         auth_title="Sign Up",
                         auth_action="Sign Up",
                         auth_switch_text="Already have an account?",
                         auth_switch_action="Sign In",
                         auth_switch_link=url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        try:
            location = request.form.get('location', '').strip()
            property_type = request.form.get('property_type', '').strip()
            bedrooms = int(request.form.get('bedrooms', 0))
            bathrooms = int(request.form.get('bathrooms', 0))
            size_sqft = float(request.form.get('size_sqft', 0))
            
            # Validate inputs
            if not location or not property_type:
                flash('Please select both location and property type', 'error')
                return redirect(url_for('predict'))
                
            if bedrooms < 1 or bathrooms < 1 or size_sqft < 1:
                flash('Please enter valid numbers for all fields', 'error')
                return redirect(url_for('predict'))
            
            # Load the model and encoders
            try:
                model = joblib.load('Encoders/rf_model_compressed_lvl2.pkl')
                location_encoder = joblib.load('Encoders/location_encoder.joblib')
                property_encoder = joblib.load('Encoders/property_encoder.joblib')
            except Exception as e:
                print(f"Error loading model or encoders: {e}")  # Debug print
                flash('Error loading prediction model', 'error')
                return redirect(url_for('predict'))
            
            # Prepare input data
            try:
                location_encoded = location_encoder.transform([location])[0]
                property_encoded = property_encoder.transform([property_type])[0]
                input_data = [[bedrooms, bathrooms, size_sqft, location_encoded, property_encoded]]
                
                # Make prediction
                predicted_price = model.predict(input_data)[0]
                
                # Record prediction in database
                conn = get_db_connection()
                try:
                    print(f"Recording prediction for user {session['user_id']}")  # Debug print
                    conn.execute('''INSERT INTO predictions 
                                  (user_id, location, property_type, bedrooms, bathrooms, size_sqft, predicted_price)
                                  VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                 (session['user_id'], location, property_type, bedrooms, bathrooms, size_sqft, predicted_price))
                    conn.commit()
                    print("Prediction recorded successfully")  # Debug print
                except sqlite3.Error as e:
                    print(f"Database error recording prediction: {e}")  # Debug print
                    flash('Error recording prediction', 'error')
                finally:
                    conn.close()
                
                return render_template('predict.html',
                                     prediction=predicted_price,
                                     form_data=request.form,
                                     counties=KENYAN_COUNTIES,
                                     property_types=PROPERTY_TYPES)
                
            except Exception as e:
                print(f"Error making prediction: {e}")  # Debug print
                flash('Error making prediction', 'error')
                return redirect(url_for('predict'))
                
        except ValueError as e:
            print(f"Value error in predict: {e}")  # Debug print
            flash('Please enter valid numbers for all fields', 'error')
            return redirect(url_for('predict'))
        except Exception as e:
            print(f"Unexpected error in predict: {e}")  # Debug print
            flash(f'Error making prediction: {str(e)}', 'error')
            return redirect(url_for('predict'))
    
    return render_template('predict.html',
                         counties=KENYAN_COUNTIES,
                         property_types=PROPERTY_TYPES)

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
            location = request.form.get('location', '').strip()
            property_type = request.form.get('property_type', '').strip()
            bedrooms = int(request.form.get('bedrooms', 0))
            bathrooms = int(request.form.get('bathrooms', 0))
            size_sqft = float(request.form.get('size_sqft', 0))
            price = float(request.form.get('price', 0))
            
            # Validate inputs
            if not location or not property_type:
                flash('Please select both location and property type', 'error')
                return redirect(url_for('add_property'))
                
            if bedrooms < 1 or bathrooms < 1 or size_sqft < 1 or price < 1:
                flash('Please enter valid numbers for all fields', 'error')
                return redirect(url_for('add_property'))
            
            conn = get_db_connection()
            try:
                print(f"Adding property data for user {session['user_id']}")  # Debug print
                conn.execute('''INSERT INTO property_data 
                              (bedrooms, bathrooms, size_sqft, location, property_type, price, added_by)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                             (bedrooms, bathrooms, size_sqft, location, property_type, price, session['user_id']))
                conn.commit()
                print("Property data added successfully")  # Debug print
                flash('Property data added successfully!', 'success')
                return redirect(url_for('home'))
            except sqlite3.Error as e:
                print(f"Database error in add_property: {e}")  # Debug print
                flash(f'Database error: {str(e)}', 'error')
                return redirect(url_for('add_property'))
            finally:
                conn.close()
        except ValueError as e:
            print(f"Value error in add_property: {e}")  # Debug print
            flash('Please enter valid numbers for all fields', 'error')
            return redirect(url_for('add_property'))
        except Exception as e:
            print(f"Unexpected error in add_property: {e}")  # Debug print
            flash(f'Error adding property: {str(e)}', 'error')
            return redirect(url_for('add_property'))
    
    return render_template('add_property.html',
                         form_action=url_for('add_property'),
                         counties=KENYAN_COUNTIES,
                         property_types=PROPERTY_TYPES)

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

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    # Run the app
    app.run(debug=True, use_reloader=False)