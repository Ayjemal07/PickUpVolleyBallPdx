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
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.get('location')

        # Create datetime objects for start and end times
        try:
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "error")
            return redirect(url_for('main.events'))

        # Validate start and end times
        if start_datetime >= end_datetime:
            flash("Start time must be before end time.", "error")
            return redirect(url_for('main.events'))

        new_event = Event(
            title=title,
            description=description,
            start_time=start_datetime,
            end_time=end_datetime,
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
        "start": f"{event.start_time.strftime('%Y-%m-%dT%H:%M:%S')}",  # Use start_time for accurate start datetime
        "end": f"{event.end_time.strftime('%Y-%m-%dT%H:%M:%S')}",  # Add end time using end_time
        "location": event.location,
        "description": event.description,
        "formatted_date": event.date.strftime("%Y-%m-%d")

        }
        for event in events
    ]
    print(events_data)

    return render_template('events.html', events=events, events_data=events_data, user_role=user_role)

@main.route('/events/edit/<int:event_id>', methods=['PUT'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()

    event.title = data.get('title')
    event.description = data.get('description')
    event.location = data.get('location')
    event.start_time = datetime.strptime(f"{data.get('date')} {data.get('start_time')}", "%Y-%m-%d %H:%M").time()
    event.end_time = datetime.strptime(f"{data.get('date')} {data.get('end_time')}", "%Y-%m-%d %H:%M").time()

    db.session.commit()
    return {'message': 'Event updated successfully'}, 200


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