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
from sqlalchemy import Text


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
    profile_image = db.Column(db.String(255), nullable=True)  
    role=db.Column(db.String(10), nullable=False, default='user')
    password_hash = db.Column(db.String(255))  # Increase to 255 characters
    token = db.Column(db.String(50))
    g_auth_verify = db.Column(db.Boolean, default=False, nullable=False)


    def __init__(self, email, first_name, last_name, role, password='', token='', g_auth_verify=False):
        self.id = self.set_id() 
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role=role

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
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(Text, nullable=False)
    image_filename = db.Column(db.String(255))
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False) 
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False, default=28)
    rsvp_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active') 
    cancellation_reason = db.Column(db.String(255), nullable=True)  # New field for cancellation reason
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ticket_price = db.Column(db.Float, nullable=False, default=10.0)
    allow_guests = db.Column(db.Boolean, default=False)
    guest_limit = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Event {self.title}>'
    


class EventAttendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='event_attendances')