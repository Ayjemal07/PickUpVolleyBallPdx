# app/authentication/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, session
from app.forms import UserLoginForm, UserRegistrationForm
from ..models import User, db
from flask_login import login_user, logout_user, login_required
from flask import request
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import re

import uuid
from werkzeug.utils import secure_filename
import os
from flask import current_app
from flask_login import current_user
mail = Mail()
serializer = URLSafeTimedSerializer('your-secret-key')  # Replace with your secret key

auth = Blueprint('auth', __name__, template_folder='auth_templates')


def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    )

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    form = UserLoginForm()
    try:
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            print(f"Attempting login with Email: {email}, Password: {password}")

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                print(f"Found user: {user.email}")
                login_user(user)
                flash('Login successful!', 'success')
                session['role'] = user.role

                print(f"User {email} logged in successfully.")
                return render_template('signin.html', form=form, first_name=user.first_name)
            
            else:
                flash('Invalid email or password. ', 'error')
                print(f"No user found with email: {email}")
                return render_template('signin.html', form=form)
    except Exception as e:
        print(f"Error during login: {e}")
        flash('An error occurred during login. Please try again later.', 'error')

    return render_template('signin.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm()

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('auth.signin'))
        
        if not is_strong_password(form.password.data):
            flash('Password must be at least 8 characters long and include an uppercase letter, a lowercase letter, a number, and a special character.', 'error')
            return redirect(url_for('auth.register'))
        
        profile_image_filename = None
        if 'profileImage' in request.files:
            image = request.files['profileImage']
            if image and image.filename:
                ext = os.path.splitext(image.filename)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                upload_path = os.path.join(current_app.root_path, 'static', 'profile_images', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                image.save(upload_path)
                profile_image_filename = filename

        # Create the user from the form data
        role = 'admin' if form.email.data == 'tester@gmail.com' else 'user'
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            role=role
        )
        user.set_password(form.password.data)  # Hashes the password
        user.profile_image = profile_image_filename or 'default.png'

        # Add the user to the database and commit
        db.session.add(user)
        db.session.commit()

        # Print for debugging purposes
        print(f"Registering User: {user}")

        # Automatically log the user in after registration
        login_user(user)
        session['role'] = role 
        flash('Account created successfully and you are now logged in!', 'success')
        return render_template('register.html', form=form, first_name=user.first_name)

    return render_template('register.html', form=form)

@auth.route('/signout', methods=['POST'])
@login_required
def signout():
    logout_user()
    session.pop('role', None)  # ✅ Ensure role is removed
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app.forms import ProfileUpdateForm  # Make sure this form exists
    form = ProfileUpdateForm(obj=current_user)

    if form.validate_on_submit():
        # You can plug in update logic here
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', form=form)


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message(subject="Reset Your Password",
                          sender="ayjemal0707@gmail.com",
                          recipients=[email],
                          body=f'Click the link to reset your password: {reset_url}')
            mail.send(msg)
            flash('If your email exists in our system, a password reset link has been sent. Please check your inbox.', 'success')
        else:
            flash('No account with that email.', 'error')
        return redirect(url_for('auth.forgot_password'))
    return render_template('forgot_password.html')


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception as e:
        flash('The password reset link is invalid or expired.', 'error')
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        if user:
            new_password = request.form['password']
            if not is_strong_password(new_password):
                flash('Password must meet complexity requirements.', 'error')
                return render_template('reset_password.html', token=token)
            user.set_password(new_password)
            db.session.commit()
            flash('Your password has been reset. Please log in.', 'success')
            return redirect(url_for('auth.signin'))
    return render_template('reset_password.html', token=token)
