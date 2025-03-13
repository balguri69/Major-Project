from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from models import User, Image
from database import db
from utils import encode_image, decode_image
import os
import uuid

routes = Blueprint('routes', __name__)

# Helper functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return file_path, unique_filename
    return None, None

# Routes
@routes.route('/')
def home():
    return render_template('home.html')

@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not fullname or not email or not password or not confirm_password:
            flash('All fields are required', 'error')
            return redirect(url_for('routes.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('routes.signup'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('routes.signup'))
        
        # Create new user
        new_user = User(fullname=fullname, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('routes.login'))
    
    return render_template('signup.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate form data
        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('routes.login'))
        
        # Check user credentials
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('routes.login'))
        
        # Log in the user
        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('routes.dashboard'))
    
    return render_template('login.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('routes.home'))

@routes.route('/dashboard')
@login_required
def dashboard():
    # Get user's images
    user_images = Image.query.filter_by(user_id=current_user.id).order_by(Image.created_at.desc()).all()
    return render_template('dashboard.html', user_images=user_images)

@routes.route('/encode', methods=['POST'])
@login_required
def encode():
    try:
        # Get form data
        message = request.form.get('message')
        if not message:
            flash('Secret message is required', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Check if file was uploaded
        if 'image' not in request.files:
            flash('No image selected', 'error')
            return redirect(url_for('routes.dashboard'))
            
        file = request.files['image']
        if file.filename == '':
            flash('No image selected', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Save the uploaded file
        file_path, unique_filename = save_uploaded_file(file)
        if not file_path:
            flash('Invalid file type', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Encode the message in the image
        encoded_filename, sha_key = encode_image(file_path, message, current_user.id)
        
        # Save encoding details to database
        new_image = Image(
            original_filename=file.filename,
            stored_filename=encoded_filename,
            sha_key=sha_key,
            message=message,
            is_encoded=True,
            user_id=current_user.id
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        flash('Image encoded successfully!', 'success')
        return redirect(url_for('routes.dashboard'))
        
    except Exception as e:
        flash(f'Error encoding image: {str(e)}', 'error')
        return redirect(url_for('routes.dashboard'))

@routes.route('/decode', methods=['POST'])
@login_required
def decode():
    try:
        # Get SHA key
        sha_key = request.form.get('sha_key')
        if not sha_key:
            flash('SHA key is required', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Check if file was uploaded
        if 'encoded_image' not in request.files:
            flash('No image selected', 'error')
            return redirect(url_for('routes.dashboard'))
            
        file = request.files['encoded_image']
        if file.filename == '':
            flash('No image selected', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Save the uploaded file
        file_path, unique_filename = save_uploaded_file(file)
        if not file_path:
            flash('Invalid file type', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Decode the message from the image
        decoded_message, generated_sha = decode_image(file_path)
        
        # Verify SHA key
        if generated_sha != sha_key:
            flash('SHA verification failed. The image might be tampered with or the wrong key was provided.', 'error')
            return redirect(url_for('routes.dashboard'))
        
        # Save decoding details to database
        new_image = Image(
            original_filename=file.filename,
            stored_filename=unique_filename,
            sha_key=sha_key,
            message=decoded_message,
            is_encoded=False,
            user_id=current_user.id
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        # Return decoded message
        return render_template('dashboard.html', 
                              decoded_message=decoded_message, 
                              user_images=Image.query.filter_by(user_id=current_user.id).order_by(Image.created_at.desc()).all())
        
    except Exception as e:
        flash(f'Error decoding image: {str(e)}', 'error')
        return redirect(url_for('routes.dashboard'))