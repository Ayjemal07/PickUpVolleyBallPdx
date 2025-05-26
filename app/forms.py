"""
This file is used to make sure our users only 
submit the right kinds of data when they're logging in. 
"""

"""package with select modules that we pull from called wtforms 
- this is also from the same origin as flask_wtf. StringField is used to ensure
user only uses string, PasswordField prevents showing it on the screen etc.
"""
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, IntegerField,FileField
from wtforms.validators import DataRequired, Email, Length
from wtforms.validators import DataRequired, Optional, EqualTo
from flask_wtf.file import FileAllowed

class UserLoginForm(FlaskForm):
    # email, password, submit
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Sign In')



class UserRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=150)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit_button = SubmitField('Create Account')



class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional()])
    last_name = StringField('Last Name', validators=[Optional()])
    profile_image = FileField('Profile Image', validators=[
        Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional(), EqualTo('new_password', message='Passwords must match')
    ])