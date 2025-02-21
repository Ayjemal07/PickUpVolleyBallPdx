# app/authentication/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, session
from app.forms import UserLoginForm, UserRegistrationForm
from ..models import User, db
from flask_login import login_user, logout_user, login_required

auth = Blueprint('auth', __name__, template_folder='auth_templates')

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

        # Create the user from the form data
        role = 'admin' if form.email.data == 'volley@test.com' else 'user'
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            role=role
        )
        user.set_password(form.password.data)  # Hashes the password

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


@auth.route('/profile')
@login_required
def profile():
    return redirect(url_for('auth.profile'))