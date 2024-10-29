import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from models import db, User
import config
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def verify_smtp_connection():
    try:
        logging.debug("Attempting to verify SMTP connection...")
        logging.debug(f"SMTP Server: {app.config['MAIL_SERVER']}, Port: {app.config['MAIL_PORT']}")
        
        with mail.connect() as conn:
            logging.info("SMTP connection successful")
            return True
    except Exception as e:
        logging.error(f"SMTP connection failed: {str(e)}")
        if "authentication failed" in str(e).lower():
            logging.error("SMTP authentication failed. Please check credentials.")
        elif "connection refused" in str(e).lower():
            logging.error("SMTP connection refused. Please check server and port settings.")
        return False

def send_password_reset_email(user):
    # First verify SMTP connection
    if not verify_smtp_connection():
        logging.error("Failed to establish SMTP connection. Cannot send reset email.")
        return False

    logging.debug(f"Generating reset token for user: {user.email}")
    token = user.get_reset_token()
    logging.debug(f"Generated reset token: {token[:10]}...")
    
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.body = f'''Hello,

You have requested to reset your password. Please click on the following link to reset your password:

{url_for('reset_password', token=token, _external=True)}

If you did not make this request, please ignore this email and no changes will be made to your account.

This link will expire in 10 minutes.

Best regards,
Your Application Team
'''
    try:
        logging.debug(f"Preparing to send reset email to: {user.email}")
        logging.debug(f"Mail configuration - Server: {app.config['MAIL_SERVER']}, Port: {app.config['MAIL_PORT']}")
        logging.debug(f"Using TLS: {app.config['MAIL_USE_TLS']}")
        logging.debug(f"Authenticating as: {app.config['MAIL_USERNAME']}")
        
        with mail.connect() as conn:
            logging.debug("SMTP connection established")
            logging.debug("Attempting to send email...")
            conn.send(msg)
            logging.info(f"Password reset email sent successfully to {user.email}")
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP Authentication failed: {str(e)}")
        logging.error("Please check MAIL_USERNAME and MAIL_PASSWORD configuration")
        return False
    except smtplib.SMTPException as e:
        logging.error(f"SMTP Error occurred: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Failed to send password reset email to {user.email}")
        logging.error(f"Error details: {str(e)}")
        logging.error(f"Mail configuration: MAIL_SERVER={app.config['MAIL_SERVER']}, MAIL_PORT={app.config['MAIL_PORT']}")
        return False

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        logging.info(f"Password reset requested for email: {email}")
        user = User.query.filter_by(email=email).first()
        if user:
            logging.debug(f"User found in database: {user.email}")
            if send_password_reset_email(user):
                flash('Check your email for the instructions to reset your password', 'info')
            else:
                flash('An error occurred sending the password reset email. Please try again later.', 'error')
            return redirect(url_for('login'))
        else:
            logging.warning(f"No user found with email: {email}")
            flash('Email address not found', 'error')
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    logging.debug(f"Password reset attempt with token: {token[:10]}...")
    user = User.verify_reset_token(token)
    if not user:
        logging.warning("Invalid or expired reset token")
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('login'))
    logging.debug(f"Valid token for user: {user.email}")
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            logging.warning("Password mismatch in reset attempt")
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)
        user.password_hash = generate_password_hash(password)
        user.reset_token = None  # Clear the reset token after successful reset
        user.reset_token_expiration = None
        db.session.commit()
        logging.info(f"Password successfully reset for user: {user.email}")
        flash('Your password has been reset', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        logging.info(f"Login attempt for email: {email}")
        user = User.query.filter_by(email=email).first()
        
        if user:
            logging.debug("User found in database")
            if check_password_hash(user.password_hash, password):
                logging.debug("Password hash check passed")
                login_user(user)
                logging.info("User logged in successfully")
                return jsonify({
                    'success': True,
                    'redirect_url': 'https://silly-sopapillas-b41c68.netlify.app',
                    'message': 'Login successful!'
                })
            else:
                logging.warning("Password hash check failed")
                return jsonify({
                    'success': False,
                    'message': 'Invalid password'
                })
        else:
            logging.warning("User not found in database")
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logging.info("Database tables created")
        
        # Check if test user exists, create if not
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            password_hash = generate_password_hash('password123', method='pbkdf2:sha256')
            test_user = User(
                email='test@example.com',
                password_hash=password_hash
            )
            db.session.add(test_user)
            db.session.commit()
            logging.info("Test user created")
    
    app.run(host='0.0.0.0', port=8000)
