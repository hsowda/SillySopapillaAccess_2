from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from models import db, User
import config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Mail
mail = Mail(app)

# Initialize SQLAlchemy
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_password_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
            flash('Check your email for the instructions to reset your password', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email address not found', 'error')
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash('Your password has been reset', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Login attempt for email: {email}")
        user = User.query.filter_by(email=email).first()
        
        if user:
            print("User found in database")
            print(f"Stored password hash: {user.password_hash}")
            if check_password_hash(user.password_hash, password):
                print("Password hash check passed")
                login_user(user)
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Create CLI command for database initialization
@app.cli.command("init-db")
def init_db():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Database initialized!")
        
        # Delete existing test user if exists
        test_user = User.query.filter_by(email='test@example.com').first()
        if test_user:
            db.session.delete(test_user)
            db.session.commit()
            print("Existing test user deleted")
        
        # Create new test user with consistent hashing method
        password_hash = generate_password_hash('password123', method='pbkdf2:sha256')
        test_user = User(
            email='test@example.com',
            password_hash=password_hash
        )
        db.session.add(test_user)
        db.session.commit()
        print(f"Test user created successfully!")
        print(f"Generated password hash: {password_hash}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create test user with consistent hashing method
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            password_hash = generate_password_hash('password123', method='pbkdf2:sha256')
            test_user = User(
                email='test@example.com',
                password_hash=password_hash
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"Test user created with hash: {password_hash}")
    app.run(host='0.0.0.0', port=8000)
