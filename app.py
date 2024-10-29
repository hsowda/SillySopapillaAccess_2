from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
import config

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

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('https://silly-sopapillas-b41c68.netlify.app')
    
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
                return redirect('https://silly-sopapillas-b41c68.netlify.app')
            else:
                print("Password hash check failed")
        else:
            print("User not found in database")
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
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
