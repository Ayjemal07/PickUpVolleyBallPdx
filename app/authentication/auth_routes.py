# app/authentication/routes.py


from flask import Blueprint, render_template, redirect, url_for, flash
from app.forms import UserLoginForm
from ..models import User, db
from flask_login import login_user, logout_user, login_required

auth = Blueprint('auth', __name__, template_folder='auth_templates')


def create_user_from_form(form_data):
    return User(
        email=form_data.get('email'),
        password=form_data.get('password'),
        first_name=form_data.get('first_name'),
        last_name=form_data.get('last_name'),
        username=form_data.get('username')
    )

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    form = UserLoginForm()
    if form.validate_on_submit():
        # Login logic here
        return redirect(url_for('main.home'))
    return render_template('signin.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = UserLoginForm()
    if form.validate_on_submit():
        # Registration logic here
        return redirect(url_for('auth.signin'))
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
