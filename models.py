from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from time import time
import jwt
from flask import current_app
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    reset_token = db.Column(db.String(300), unique=True)
    reset_token_expiration = db.Column(db.DateTime)
    
    def get_reset_token(self, expires_in=600):  # 10 minutes expiration
        token = jwt.encode(
            {
                'reset_password': self.id,
                'exp': time() + expires_in,
                'iat': time()  # issued at time
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        # Store token and expiration in database
        self.reset_token = token
        self.reset_token_expiration = datetime.utcnow() + timedelta(seconds=expires_in)
        db.session.commit()
        return token

    @staticmethod
    def verify_reset_token(token):
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            user_id = payload['reset_password']
            user = User.query.get(user_id)
            
            # Additional verification checks
            if not user or not user.reset_token:
                print("No user found or no reset token")
                return None
                
            if user.reset_token != token:
                print("Token mismatch")
                return None
                
            if datetime.utcnow() > user.reset_token_expiration:
                print("Token has expired")
                return None
                
            return user
            
        except jwt.ExpiredSignatureError:
            print("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid JWT token")
            return None
        except Exception as e:
            print(f"Error verifying token: {str(e)}")
            return None

    def __repr__(self):
        return f'<User {self.email}>'
