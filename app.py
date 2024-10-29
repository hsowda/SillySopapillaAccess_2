from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
import config
import os

app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize SQLAlchemy
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'true'
        
        print(f"Login attempt for email: {email}")
        user = User.query.filter_by(email=email).first()
        
        if user:
            print("User found in database")
            if check_password_hash(user.password_hash, password):
                print("Password hash check passed")
                login_user(user, remember=remember)
                if remember:
                    token = user.generate_remember_token()
                    db.session.commit()
                print("User logged in successfully")
                return jsonify({
                    'success': True,
                    'redirect_url': 'https://silly-sopapillas-b41c68.netlify.app',
                    'message': 'Login successful!'
                })
            else:
                print("Password hash check failed")
                return jsonify({
                    'success': False,
                    'message': 'Invalid password'
                })
        else:
            print("User not found in database")
            return jsonify({
                'success': False,
                'message': 'User not found'
            })
    
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.bio = request.form.get('bio')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            
    return redirect(url_for('profile'))

@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        current_user.remember_token = None
        db.session.commit()
    logout_user()
    return redirect(url_for('login'))

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        # Create test user if it doesn't exist
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            password_hash = generate_password_hash('password123', method='pbkdf2:sha256')
            test_user = User(
                email='test@example.com',
                password_hash=password_hash,
                first_name='Test',
                last_name='User',
                bio='This is a test user account.'
            )
            db.session.add(test_user)
            db.session.commit()

if __name__ == '__main__':
    init_db()  # Initialize database with new schema
    app.run(host='0.0.0.0', port=8000)
