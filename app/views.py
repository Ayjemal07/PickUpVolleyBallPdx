# This file handles the routes

from flask import Blueprint, render_template, redirect, url_for, flash, session 

from .models import Event, User, db

from flask import request
from datetime import datetime

import os
from flask import current_app
from werkzeug.utils import secure_filename


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
        
    # Get list of image filenames
    image_folder = os.path.join(current_app.root_path, 'static', 'images')
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    
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

    for event in events:
        event.formatted_date = event.date.strftime('%b %d, %Y')

    events_data = [
        {
        "id": event.id,   
        "title": event.title,
        "start": f"{event.date.strftime('%Y-%m-%d')}T{event.start_time.strftime('%H:%M')}",  # No seconds
        "end": f"{event.date.strftime('%Y-%m-%d')}T{event.end_time.strftime('%H:%M')}",  # No seconds
        "location": event.location,
        "description": event.description,
        "formatted_date": event.formatted_date,
        "status": event.status,
        "cancellation_reason": event.cancellation_reason

        }
        for event in events
    ]
    print(events_data)
    for event in events:
        print(f"ID: {event.id}, Title: {event.title}, Formatted Date: {event.formatted_date if hasattr(event, 'formatted_date') else 'MISSING'}")

    return render_template('events.html', events=events, events_data=events_data, user_role=user_role,image_files=image_files)

#Route to add an event
@main.route('/events/add', methods=['POST'])
def add_event():
    user_role = session.get('role', 'user')
    
    if user_role != 'admin':
        return {'error': 'Unauthorized'}, 403

    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    location = request.form.get('location')
    image_filename = None

    image_filename = None

    # Handle uploaded file
    if 'eventImage' in request.files:
        image = request.files['eventImage']
        if image and image.filename:
            filename = secure_filename(image.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'images', filename)
            image.save(upload_path)
            image_filename = filename
    
    # Handle existing image option
    elif request.form.get('existingImage'):
        image_filename = request.form.get('existingImage')

    try:
        start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        event_date = datetime.strptime(date, "%Y-%m-%d").date()

    except ValueError:
        return {'error': 'Invalid date or time format'}, 400

    new_event = Event(
        title=title,
        description=description,
        date=event_date,
        start_time=start_datetime,
        end_time=end_datetime,
        location=location,
        image_filename=image_filename,
        status='active'
    )
    db.session.add(new_event)
    db.session.commit()
    print(f"Event for {date} {start_time} has been posted")

    return {'message': 'Event added successfully'}, 201

#Route to edit an event
@main.route('/events/edit/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()

    try:
        event.title = data.get('title')
        event.description = data.get('description')
        event.location = data.get('location')
        event.date = datetime.strptime(data.get('date'), "%Y-%m-%d").date()
        event.start_time = datetime.strptime(data.get('start_time'), "%H:%M").time()  # Adjust time parsing
        event.end_time = datetime.strptime(data.get('end_time'), "%H:%M").time()  # Adjust time parsing

        db.session.commit()
        return {'message': 'Event updated successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 400

@main.route('/events/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return {'message': 'Event deleted successfully'}, 200


@main.route('/events/cancel/<int:event_id>', methods=['POST'])
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()
    event.status = 'canceled'
    event.cancellation_reason = data.get('cancellation_reason', 'Cancelled Event, contact event organizer')
    
    db.session.commit()
    return {'message': 'Event canceled successfully'}, 200



@main.route('/events/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    event.formatted_date = event.date.strftime('%b %d, %Y')
    return render_template('event_details.html', event=event)

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



#paypal logic starts here:

import json
import os
import requests
from flask import jsonify, request

# PayPal credentials (use your actual client ID/secret or load from env)
PAYPAL_CLIENT_ID = "AaeOK9F7Bor-M4-yDY_0li_nPkLIXo0Ul0vuW5EVUEdJmOj9nIbryb_lCe5Lt-wODB-lPqUS7REXtqTx"
PAYPAL_SECRET = "EKOLBO_CdpzLvMZ9q7yWNzgFQj7srp00Sntt1a3kBF5-b2l5zcH9QmDCa_-5vzLu8wVqReTlhpiTiboN"
PAYPAL_BASE = "https://api-m.sandbox.paypal.com"  # use live URL when in production

def get_access_token():
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    headers = { "Accept": "application/json", "Accept-Language": "en_US" }
    data = { "grant_type": "client_credentials" }
    response = requests.post(f"{PAYPAL_BASE}/v1/oauth2/token", headers=headers, data=data, auth=auth)
    return response.json()["access_token"]

@main.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    cart = data.get("cart", [])

    access_token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


    total = 0
    for item in cart:
        quantity = item.get("quantity", 1)
        total += quantity * 10  # $10 per ticket

    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": f"{total:.2f}"
            }
        }]
    }
    response = requests.post(f"{PAYPAL_BASE}/v2/checkout/orders", headers=headers, json=body)
    return jsonify(response.json())

@main.route("/api/orders/<order_id>/capture", methods=["POST"])
def capture_order(order_id):
    access_token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture", headers=headers)
    return jsonify(response.json())
