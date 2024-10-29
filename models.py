from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    remember_token = db.Column(db.String(100), unique=True)
    
    # Profile fields
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))
    
    def get_id(self):
        return str(self.id)
    
    def generate_remember_token(self):
        self.remember_token = secrets.token_urlsafe(32)
        return self.remember_token

    def __repr__(self):
        return f'<User {self.email}>'
