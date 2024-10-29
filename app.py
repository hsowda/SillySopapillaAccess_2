from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from models import db, User
import config
import os

app = Flask(__name__)
app.config.from_object(config.Config)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize SQLAlchemy
db.init_app(app)

# Initialize serializer for generating secure tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_password_reset_email(user_email):
    token = serializer.dumps(user_email, salt='password-reset-salt')
    reset_url = url_for('reset_password', token=token, _external=True)
    
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user_email])
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.
'''
    mail.send(msg)

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

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                send_password_reset_email(user.email)
                flash('Check your email for the instructions to reset your password', 'info')
            except Exception as e:
                app.logger.error(f"Error sending password reset email: {str(e)}")
                flash('Error sending password reset email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists in database
            flash('If this email exists in our database, you will receive reset instructions.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token expires after 1 hour
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid or expired reset link', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('reset_password.html')
            
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            flash('Your password has been reset', 'success')
            return redirect(url_for('login'))
        
        return render_template('reset_password.html')
    
    except Exception as e:
        app.logger.error(f"Error in password reset: {str(e)}")
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create test user if it doesn't exist
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            password_hash = generate_password_hash('password123', method='pbkdf2:sha256')
            test_user = User(
                email='test@example.com',
                password_hash=password_hash
            )
            db.session.add(test_user)
            db.session.commit()
    app.run(host='0.0.0.0', port=8000)
