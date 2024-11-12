"""
This file is used to make sure our users only 
submit the right kinds of data when they're logging in. 
"""

"""package with select modules that we pull from called wtforms 
- this is also from the same origin as flask_wtf. StringField is used to ensure
user only uses string, PasswordField prevents showing it on the screen etc.
"""
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email

class UserLoginForm(FlaskForm):
    # email, password, submit
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit_button = SubmitField()


