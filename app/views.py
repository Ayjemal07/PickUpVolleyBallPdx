# This file handles the routes

from flask import Blueprint, render_template, redirect, url_for, flash, session 

from .models import Event, User, db
import traceback
from flask import request, jsonify # Import jsonify
from datetime import datetime

import os
from flask import current_app
from werkzeug.utils import secure_filename
import uuid 

from .models import EventAttendee
from flask_login import current_user, login_required # Import login_required



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
    user_id = session.get('user_id') or (current_user.id if current_user.is_authenticated else None)
    print("User ID in session:", user_id)
        
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
        allow_guests = request.form.get('allow_guests') == 'on'
        guest_limit = int(request.form.get('guest_limit') or 0)
        ticket_price = float(request.form.get('ticket_price') or 0.0)
        max_capacity = int(request.form.get('max_capacity') or 28)

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
            start_time=start_datetime.time(), # Store only time
            end_time=end_datetime.time(),     # Store only time
            location=location,
            status='active',
            allow_guests=allow_guests,
            guest_limit=guest_limit,
            ticket_price=ticket_price,
            max_capacity=max_capacity,
            date=datetime.strptime(date, "%Y-%m-%d").date()
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Event added successfully!', 'success')  # Flash success message

        return redirect(url_for('main.events'))
    
    # Fetch all events sorted by date
    events = Event.query.order_by(Event.date.asc()).all()

    for event in events:
        event.formatted_date = event.date.strftime('%b %d, %Y')
        attendees = EventAttendee.query.filter_by(event_id=event.id).all()
        event.rsvp_count = sum(1 + (a.guest_count or 0) for a in attendees)
        event.is_attending = any(a.user_id == user_id for a in attendees)
        print(f"User {user_id} attending event {event.id}? {event.is_attending}")


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
        "cancellation_reason": event.cancellation_reason,
        "allow_guests": event.allow_guests,
        "guest_limit": event.guest_limit,
        "ticket_price": event.ticket_price,
        "max_capacity": event.max_capacity,
        "rsvp_count": event.rsvp_count,
        "is_attending": event.is_attending,
        'image_filename': event.image_filename

        }
        for event in events
    ]
    for event in events:
        print(f"ID: {event.id}, Title: {event.title}, Formatted Date: {event.formatted_date if hasattr(event, 'formatted_date') else 'MISSING'}")

    return render_template('events.html', events=events, events_data=events_data, user_role=user_role,image_files=image_files)

#Route to add an event
@main.route('/events/add', methods=['POST'])
def add_event():
    user_role = session.get('role', 'user')
    
    if user_role != 'admin':
        return {'error': 'Unauthorized'}, 403

    data = request.get_json() # Use get_json() for data sent via fetch with JSON.stringify
    title = data.get('title')
    description = data.get('description')
    date_str = data.get('date')
    start_time_str = data.get('startTime')
    end_time_str = data.get('endTime')
    location = data.get('location')

    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()

    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400

    new_event = Event(
        title=title,
        description=description,
        date=event_date,
        start_time=start_time_obj,
        end_time=end_time_obj,
        location=location,
        # image_filename=image_filename, # Add if you handle image here
        status='active',
        # allow_guests=allow_guests, # Add if you handle these fields here
        # guest_limit=guest_limit,
        # ticket_price=ticket_price,
        # max_capacity=max_capacity
    )
    db.session.add(new_event)
    db.session.commit()

    return jsonify({'message': 'Event added successfully'}), 201

#Route to edit an event
@main.route('/events/edit/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json() # Use get_json() for data sent via fetch with JSON.stringify

    try:
        # Handle basic text inputs
        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        event.location = data.get('location', event.location)
        
        date_str = data.get('date')
        if date_str:
            event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        start_time_str = data.get('start_time')
        if start_time_str:
            event.start_time = datetime.strptime(start_time_str, "%H:%M").time()
        
        end_time_str = data.get('end_time')
        if end_time_str:
            event.end_time = datetime.strptime(end_time_str, "%H:%M").time()

        # Optional fields (assuming these are sent via JSON for edit)
        event.allow_guests = data.get('allow_guests', event.allow_guests)
        event.guest_limit = int(data.get('guest_limit', event.guest_limit))
        event.ticket_price = float(data.get('ticket_price', event.ticket_price))
        event.max_capacity = int(data.get('max_capacity', event.max_capacity))

        # Image handling logic needs to be adapted if it's sent via JSON or separate endpoint
        # For now, assuming image updates are not part of this JSON edit endpoint
        # if 'eventImage' in request.files: ...
        # elif request.form.get('existingImage'): ...

        db.session.commit()
        return jsonify({'success': True, 'message': 'Event updated successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@main.route('/events/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted successfully'}), 200


@main.route('/events/cancel/<int:event_id>', methods=['POST'])
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()
    event.status = 'canceled'
    event.cancellation_reason = data.get('cancellation_reason', 'Cancelled Event, contact event organizer')
    
    db.session.commit()
    return jsonify({'message': 'Event canceled successfully'}), 200



# event_details()
@main.route('/events/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    event.formatted_date = event.date.strftime('%b %d, %Y')
    attendees = EventAttendee.query.filter_by(event_id=event.id).all()
    event.rsvp_count = sum(1 + (a.guest_count or 0) for a in attendees)
    user_id = session.get('user_id') or (current_user.id if current_user.is_authenticated else None)
    is_attending = any(a.user_id == user_id for a in attendees)

    event_dict = {
        "id": event.id,
        "title": event.title,
        "location": event.location,
        "description": event.description,
        "start": event.start_time.strftime('%Y-%m-%dT%H:%M'),
        "end": event.end_time.strftime('%Y-%m-%dT%H:%M'),
        "formatted_date": event.formatted_date,
        "status": event.status,
        "cancellation_reason": event.cancellation_reason,
        "allow_guests": event.allow_guests,
        "guest_limit": event.guest_limit,
        "ticket_price": float(event.ticket_price),
        "max_capacity": event.max_capacity,
        "rsvp_count": event.rsvp_count
    }


    return render_template('event_details.html', event=event, event_data=event_dict, attendees=attendees,is_attending=is_attending)


# New endpoint to fetch user's RSVP for an event
@main.route("/api/user_rsvp/<int:event_id>", methods=['GET'])
@login_required 
def get_user_rsvp(event_id):
    user_id = current_user.id
    rsvp = EventAttendee.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    if rsvp:
        user = User.query.get(user_id)
        return jsonify({
            'rsvp_id': rsvp.id,
            'guest_count': rsvp.guest_count,
            'user_first_name': user.first_name,
            'user_last_name': user.last_name
        }), 200
    else:
        return jsonify({'error': 'RSVP not found for this user and event'}), 404


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
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.json()["access_token"]

@main.route("/api/orders", methods=["POST"])
@login_required # Ensure user is logged in
def create_order():
    data = request.get_json()
    event_id = data.get("event_id")
    requested_quantity = data.get("quantity", 1) # Total quantity (1 attendee + guests)
    is_edit = data.get("is_edit", False)
    rsvp_id = data.get("rsvp_id")
    initial_guest_count = data.get("initial_guest_count", 0)

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    ticket_price = event.ticket_price

    # Calculate the amount to charge based on whether it's an edit or initial RSVP
    amount_to_charge = 0.0
    if is_edit:
        # For edits, calculate the difference in guests
        # requested_quantity is (1 + new_guests)
        # initial_quantity is (1 + initial_guests)
        initial_quantity = 1 + initial_guest_count
        guest_difference = requested_quantity - initial_quantity
        amount_to_charge = guest_difference * ticket_price
        
        # If amount_to_charge is negative, it means a refund is due.
        # PayPal's createOrder doesn't handle negative amounts directly for refunds.
        # You'd typically process refunds after capture or via a separate API call.
        # For this example, we'll only create an order for positive differences.
        if amount_to_charge < 0:
            # If guests are decreased, no new payment is needed.
            # The refund logic would be handled after the RSVP update in capture.
            return jsonify({"error": "Decreasing guests does not require a new payment. Please proceed to update RSVP."}), 400
        elif amount_to_charge == 0:
            # If guest count is unchanged, no payment needed.
            return jsonify({"error": "No change in guest count, no payment needed."}), 400
            
    else:
        # Initial RSVP: charge for all attendees (1 + guests)
        amount_to_charge = requested_quantity * ticket_price

    if amount_to_charge <= 0:
        return jsonify({"error": "Invalid amount to charge."}), 400


    access_token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": f"{amount_to_charge:.2f}"
            },
            "custom_id": f"{event_id}-{current_user.id}-{is_edit}-{rsvp_id if rsvp_id else ''}-{initial_guest_count}" # Pass custom data
        }]
    }
    response = requests.post(f"{PAYPAL_BASE}/v2/checkout/orders", headers=headers, json=body)
    response.raise_for_status()
    return jsonify(response.json())

@main.route("/api/orders/<order_id>/capture", methods=["POST"])
@login_required # Ensure user is logged in
def capture_order(order_id):
    try:
        user_id = current_user.id
        data = request.get_json()

        event_id = data.get("event_id")
        new_guest_count = int(data.get("guest_count", 0))
        is_edit = data.get("is_edit", False)
        rsvp_id = data.get("rsvp_id")


        event = Event.query.get(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404

        # PayPal capture logic
        access_token = get_access_token()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
        capture_response = requests.post(f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture", headers=headers)
        capture_response.raise_for_status()
        order_data = capture_response.json()

        if order_data.get("status") != "COMPLETED":
            return jsonify({"error": f"PayPal transaction not completed: {order_data.get('status')}"}), 400

        if is_edit:
            attendee = EventAttendee.query.get(rsvp_id)
            if not attendee:
                return jsonify({"error": "Existing RSVP not found"}), 404
            
            attendee.guest_count = new_guest_count
            success_message = f'Your RSVP for {event.title} has been updated!'

        else: # Initial RSVP
            attendee = EventAttendee(event_id=event_id, user_id=user_id, guest_count=new_guest_count)
            db.session.add(attendee)
            success_message = f"You're confirmed for {event.title}! See you there!"
        # Recalculate total RSVP count for the event
        all_attendees_for_event = EventAttendee.query.filter_by(event_id=event_id).all()
        event.rsvp_count = sum(1 + (a.guest_count or 0) for a in all_attendees_for_event)

        db.session.commit()

        # Add the message to the JSON response
        order_data['success_message'] = success_message

    except Exception as e:
        traceback.print_exc()
        print("--- END OF CRITICAL ERROR ---\n")
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500

    return jsonify(order_data)

