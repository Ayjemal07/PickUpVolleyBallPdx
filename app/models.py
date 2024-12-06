#Models are used for creating classes that are used repeatedly 
# to populate databases.

#UUID stands for universally unique identifiers. 
#These are great for creating independent items that won't clash with other items
import uuid 

#imports date and time
from datetime import datetime


#Werkzeug is a security package. This allows us to make the password data that we store in our 
#database secret, so that if we log in to look at our database, 
#we can't see what users saved as their password!
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_login import LoginManager
import secrets
from flask_sqlalchemy import SQLAlchemy
from enum import Enum


db = SQLAlchemy()

# set variables for class instantiation
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID is 36 characters long
    first_name=db.Column(db.String(150), nullable=False)
    last_name=db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))  # Increase to 255 characters
    token = db.Column(db.String(50))
    g_auth_verify = db.Column(db.Boolean, default=False)


    def __init__(self, email, first_name, last_name, password='', token='', g_auth_verify=False):
        self.id = self.set_id() 
        self.email = email
        self.password = self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name

        self.token = self.set_token(24)

    def set_token(self, length):
        return secrets.token_hex(length)

    def set_id(self):
        return str(uuid.uuid4())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'User {self.email} has been added to the database'
    



class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False, default=28)
    rsvp_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='draft')  # 'draft', 'published', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.name}>'
    

