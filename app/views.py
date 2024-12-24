# This file handles the routes

from flask import Blueprint, render_template, redirect, url_for, flash, session 

from .models import Event, User, db

from flask import request
from datetime import datetime


main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html', embedded=False)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/events', methods=['GET', 'POST'])
def events():
    user_role = session.get('role', 'user')  # Default to 'user'
    
    # For admin: Handle event creation if the form is submitted
    if request.method == 'POST' and user_role == 'admin':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')

        print(f"Received form data: title={title}, date={date}, time={time}, location={location}")
        new_event = Event(
            title=title,
            description=description,
            date=date,
            time=time,
            location=location,
            status='active'
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Event added successfully!', 'success')  # Flash success message

        return redirect(url_for('main.events'))
    
    # Fetch all events sorted by date
    events = Event.query.order_by(Event.date.asc()).all()
    events_data = [
        {
            "title": event.title,
            "start": f"{event.date}T{event.time}",
            "location": event.location,
            "description": event.description,
            "formatted_date": event.date.strftime("%Y-%m-%d")

        }
        for event in events
    ]

    return render_template('events.html', events=events, events_data=events_data, user_role=user_role)



@main.route('/subscriptions')
def subscriptions():
    return render_template('subscriptions.html')

@main.route('/hosting')
def hosting():
    return render_template('hosting.html')


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/contactus')
def contactus():
    return render_template('contactus.html')