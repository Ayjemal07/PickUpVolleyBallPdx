# This file handles the routes

from flask import Blueprint, render_template, redirect, url_for, flash, session 
import urllib.parse

from .models import Event, User, db
import traceback
from flask import request, jsonify # Import jsonify
from datetime import datetime, timedelta, date

import os
from flask import current_app
from werkzeug.utils import secure_filename
import uuid 
from flask_login import current_user

from .models import EventAttendee
from flask_login import current_user, login_required # Import login_required
from flask_mail import Mail, Message
mail = Mail()

import os
from dotenv import load_dotenv
import requests


load_dotenv() # Load variables from .env file



main = Blueprint('main', __name__)

# PayPal credentials
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_PLAN_ID = os.getenv("PAYPAL_PLAN_ID") # Make sure to add this to your .env file
PAYPAL_BASE = "https://api-m.paypal.com" 

def send_subscription_email(user_email):
    body = """
    Thank you for subscribing to Pick Up Volleyball events, we are excited to have you join and be part of our community! 

    You can view and sign up for all events using this link: https://pickupvolleyballpdx.com/events

    Subscriptions will renew every 30 days starting from the time of purchase, with 4 new event credits being issued every cycle. Event credits cannot be used for guests, and any unused credits will not roll over. 

    Please note that subscriptions must be managed with Paypal directly, and cannot be canceled/updated from your Pick Up Volleyball Profile. This function will become available in future releases. 

    See you out there!
    """

    msg = Message(
        subject="Subscription Receipt Email",
        recipients=[user_email],
        body=body.strip()
    )
    print(f"Attempting to send subscription email to: {user_email}") # <--- ADD THIS LINE
    mail.send(msg)
    print("Email send attempt completed.") # <--- AND THIS LINE

@main.route('/')
def home():
    return render_template('home.html', embedded=False)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/events', methods=['GET', 'POST'])
def events():
    user_role = session.get('role', 'user')  # Default to 'user'
    is_authenticated = current_user.is_authenticated # Get the login status

    # Get list of image filenames
    image_folder = os.path.join(current_app.root_path, 'static', 'images')
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    # For admin: Handle event creation if the form is submitted
    if request.method == 'POST' and user_role == 'admin':
        # This section remains unchanged...
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.get('location')
        full_address = request.form.get('full_address') # Get the new field
        allow_guests = request.form.get('allow_guests') == 'on'
        guest_limit = int(request.form.get('guest_limit') or 0)
        ticket_price = float(request.form.get('ticket_price') or 0.0)
        max_capacity = int(request.form.get('max_capacity') or 28)


        # --- CORRECTED IMAGE HANDLING LOGIC ---
        image_filename = None
        # Priority 1: A new file was uploaded.
        image_file = request.files.get('eventImage')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            save_path = os.path.join(current_app.root_path, 'static/images', unique_filename)
            image_file.save(save_path)
            image_filename = unique_filename
        # Priority 2: No new file, but an existing image was selected.
        elif request.form.get('existingImage'):
            image_filename = request.form.get('existingImage')

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
            full_address = full_address,
            status='active',
            allow_guests=allow_guests,
            guest_limit=guest_limit,
            ticket_price=ticket_price,
            max_capacity=max_capacity,
            date=datetime.strptime(date, "%Y-%m-%d").date(),
            image_filename=image_filename
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event added successfully!', 'success')
        return redirect(url_for('main.events'))
    
    # --- NEW LOGIC for sorting, auto-deleting, and preparing events ---
    now = now = datetime.now()
    two_months_ago = now.date() - timedelta(days=60)

    # 1. Automatically delete events older than two months
    events_to_delete = Event.query.filter(Event.date < two_months_ago).all()
    for event in events_to_delete:
        EventAttendee.query.filter_by(event_id=event.id).delete() # Clean up RSVPs
        db.session.delete(event)
    if events_to_delete:
        db.session.commit()

    # 2. Fetch all events that are not yet deleted
    displayable_events = Event.query.filter(Event.date >= two_months_ago).order_by(Event.date.asc()).all()

    upcoming_events = []
    past_events = []

    for event in displayable_events:
        # Combine the event's date and end_time into a single datetime object
        event_end_datetime = datetime.combine(event.date, event.end_time)

        # If the event's end time is in the future, it's an upcoming event
        if event_end_datetime >= now:
            upcoming_events.append(event)
        else:
            # Otherwise, it's a past event
            past_events.append(event)
            
    # 3. Sort past events descending to get the most recent, and limit to 2
    past_events.sort(key=lambda x: x.date, reverse=True)
    past_events_display = past_events[:2]

    # 4. Process event data for the template
    user_id = session.get('user_id') or (current_user.id if current_user.is_authenticated else None)

    db.session.commit()


    def process_event_list(event_list):
        with db.session.no_autoflush:
            for event in event_list:
                event.formatted_date = event.date.strftime('%b %d, %Y')
                attendees = EventAttendee.query.filter_by(event_id=event.id).all()
                event.rsvp_count = sum(1 + (a.guest_count or 0) for a in attendees)
                event.is_attending = any(a.user_id == user_id for a in attendees)
    
    
    process_event_list(upcoming_events)
    process_event_list(past_events_display)

    def create_event_dict(event, is_past=False):
        return {
            "id": event.id,   
            "title": event.title,
            # Combine date and time before formatting
            "start": datetime.combine(event.date, event.start_time).isoformat(),
            "end": datetime.combine(event.date, event.end_time).isoformat(),
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
            'image_filename': event.image_filename,
            'is_past': is_past
        }

    upcoming_events_data = [create_event_dict(e, is_past=False) for e in upcoming_events]
    past_events_data = [create_event_dict(e, is_past=True) for e in past_events_display]
    
    # Combine data for the FullCalendar view
    all_events_for_calendar = upcoming_events_data + past_events_data

    user_has_free_event = False
    if current_user.is_authenticated and not current_user.has_used_free_event:
        user_has_free_event = True

    user_credits = 0
    user_expiry_date = None
    if current_user.is_authenticated:
        user_credits = current_user.event_credits
        if current_user.subscription_expiry_date:
            user_expiry_date = current_user.subscription_expiry_date.isoformat()

    print("PayPal Client ID:", PAYPAL_CLIENT_ID)
    return render_template('events.html', 
                           upcoming_events_data=upcoming_events_data,
                           past_events_data=past_events_data,
                           all_events_for_calendar=all_events_for_calendar,
                           user_role=user_role,
                           user_has_free_event=user_has_free_event,
                           user_event_credits=user_credits,
                           user_subscription_expiry_date=user_expiry_date,
                           image_files=image_files,is_authenticated=is_authenticated,
                           paypal_client_id=PAYPAL_CLIENT_ID)


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
        status='active',

    )
    db.session.add(new_event)
    db.session.commit()

    return jsonify({'message': 'Event added successfully'}), 201

#Route to edit an event
@main.route('/events/edit/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    try:
        # Update event fields from form data
        event.title = request.form.get('title', event.title)
        event.description = request.form.get('description', event.description)
        event.location = request.form.get('location', event.location)
        event.full_address = request.form.get('full_address', event.full_address) # Add this line

        
        date_str = request.form.get('date')
        if date_str:
            event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        start_time_str = request.form.get('start_time')
        if start_time_str:
            event.start_time = datetime.strptime(start_time_str, "%H:%M").time()
        
        end_time_str = request.form.get('end_time')
        if end_time_str:
            event.end_time = datetime.strptime(end_time_str, "%H:%M").time()

        event.allow_guests = request.form.get('allow_guests') == 'on'
        event.guest_limit = int(request.form.get('guest_limit', event.guest_limit))
        event.ticket_price = float(request.form.get('ticket_price', event.ticket_price))
        event.max_capacity = int(request.form.get('max_capacity', event.max_capacity))
        
        # Handle image update
        image_file = request.files.get('eventImage')
        if image_file and image_file.filename != '':
                filename = secure_filename(image_file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                save_path = os.path.join(current_app.root_path, 'static/images', unique_filename)
                image_file.save(save_path)
                event.image_filename = unique_filename
        elif request.form.get('existingImage'):
             event.image_filename = request.form.get('existingImage')

        db.session.commit()
        flash('Event updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating event: {e}', 'error')

    return redirect(url_for('main.events'))

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


    # Generate Google Maps link
    maps_link = None
    if event.full_address:
        maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(event.full_address)}"

    event_dict = {
        "id": event.id,
        "title": event.title,
        "location": event.location,
        "full_address": event.full_address,
        "description": event.description,
        "start": datetime.combine(event.date, event.start_time).isoformat(),
        "end": datetime.combine(event.date, event.end_time).isoformat(),
        "formatted_date": event.formatted_date,
        "status": event.status,
        "cancellation_reason": event.cancellation_reason,
        "allow_guests": event.allow_guests,
        "guest_limit": event.guest_limit,
        "ticket_price": float(event.ticket_price),
        "max_capacity": event.max_capacity,
        "rsvp_count": event.rsvp_count,
        "image_filename": event.image_filename,
        "is_attending": is_attending
    }

    user_has_free_event = False
    user_credits = 0
    user_expiry_date = None
    if current_user.is_authenticated:
        if not current_user.has_used_free_event:
            user_has_free_event = True
        user_credits = current_user.event_credits
        if current_user.subscription_expiry_date:
            user_expiry_date = current_user.subscription_expiry_date.isoformat()

    return render_template(
        'event_details.html', 
        event=event, 
        event_data=event_dict, 
        attendees=attendees,
        is_attending=is_attending,
        maps_link=maps_link,
        user_has_free_event=user_has_free_event,
        user_event_credits=user_credits,
        user_subscription_expiry_date=user_expiry_date,
        paypal_client_id=PAYPAL_CLIENT_ID,
        is_authenticated=current_user.is_authenticated,
        user_role=current_user.role if current_user.is_authenticated else 'user'
    )


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
            'first_name': user.first_name,
            'last_name': user.last_name
        }), 200
    else:
        return jsonify({'error': 'RSVP not found for this user and event'}), 404


@main.route('/subscriptions')
def subscriptions():
    return render_template('subscriptions.html', paypal_client_id=PAYPAL_CLIENT_ID)

@main.route('/hosting')
def hosting():
    return render_template('hosting.html')


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/contactus')
def contactus():
    return render_template('contactus.html')




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

    current_attendees = EventAttendee.query.filter_by(event_id=event.id).all()
    current_rsvp_count = sum(1 + (a.guest_count or 0) for a in current_attendees)
    
    # For edits, we only check against capacity if new people are being added.
    if is_edit:
        # Calculate how many people are being *added* in this edit.
        new_guest_count = requested_quantity - 1
        additional_attendees = new_guest_count - initial_guest_count
        if additional_attendees > 0 and (current_rsvp_count + additional_attendees > event.max_capacity):
             return jsonify({"error": f"Sorry, the event does not have enough space to add {additional_attendees} more person(s)."}), 400
    else: # For new RSVPs
        # Check if adding the requested number of people exceeds capacity.
        if current_rsvp_count + requested_quantity > event.max_capacity:
            # Calculate remaining spots for a more helpful error message.
            spots_left = event.max_capacity - current_rsvp_count
            return jsonify({"error": f"Sorry, this event is full or does not have enough space. Only {spots_left} spot(s) remaining."}), 400
    # --- Bug Fix End ---

    ticket_price = event.ticket_price
    user = current_user

    # Calculate the amount to charge based on whether it's an edit or initial RSVP
    amount_to_charge = 0.0
    if is_edit:
        # For edits, calculate the difference in guests (this logic remains the same)
        initial_quantity = 1 + initial_guest_count
        guest_difference = requested_quantity - initial_quantity
        amount_to_charge = guest_difference * ticket_price
        
        if amount_to_charge <= 0:
            return jsonify({"error": "No payment required for this change."}), 400
            
    else:
        # --- NEW LOGIC FOR INITIAL RSVP ---
        # By default, we assume everyone needs to be paid for.
        payable_attendees = requested_quantity

        # Check if the user's own spot is covered by a benefit.
        # This logic mirrors the frontend checks for precedence.
        is_subscription_active = user.event_credits > 0 and (user.subscription_expiry_date is None or user.subscription_expiry_date >= date.today())
        
        if not user.has_used_free_event:
            # First free event applies, so charge for one less person (i.e., only guests).
            payable_attendees -= 1
        elif is_subscription_active:
            # A subscription credit applies, so charge for one less person.
            payable_attendees -= 1
            
        payable_attendees = max(0, payable_attendees)
        
        amount_to_charge = payable_attendees * ticket_price

    if amount_to_charge <= 0:
        # This case should now only be hit if a free/credit user has no guests,
        # which is handled by the non-payment flow on the frontend.
        # This check is a safeguard.
        return jsonify({"error": "No payment is required for this RSVP."}), 400


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
        user = current_user
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
            attendee = EventAttendee(event_id=event_id, user_id=user.id, guest_count=new_guest_count)
            db.session.add(attendee)

            # --- NEW & CORRECTED BENEFIT LOGIC ---
            # Determine which benefit was used to cover the user's own spot.
            is_subscription_active = user.event_credits > 0 and (user.subscription_expiry_date is None or user.subscription_expiry_date >= date.today())
            
            # Priority 1: Was the first free event used?
            if not user.has_used_free_event:
                user.has_used_free_event = True
            # Priority 2: If not, was a subscription credit used for their spot?
            elif is_subscription_active:
                user.event_credits -= 1 # Decrement the credit balance
            # --- END OF CORRECTED LOGIC ---

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


@main.route("/api/paypal/create-subscription", methods=["POST"])
@login_required
def create_paypal_subscription():
    """
    Creates a PayPal subscription for the logged-in user.
    """
    if not PAYPAL_PLAN_ID:
        return jsonify({"error": "Subscription plan is not configured on the server."}), 500

    access_token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    # The custom_id is crucial. We pass the user's ID to identify them in the webhook.
    body = {
        "plan_id": PAYPAL_PLAN_ID,
        "custom_id": current_user.id,
        "application_context": {
            "return_url": url_for('main.events', _external=True) + '?sub_status=pending',  # Add query param here
            "cancel_url": url_for('main.subscriptions', _external=True)
        }
    }
    
    try:
        response = requests.post(f"{PAYPAL_BASE}/v1/billing/subscriptions", headers=headers, json=body)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.HTTPError as err:
        print(f"PayPal API Error: {err.response.text}")
        return jsonify({"error": "Could not create subscription with PayPal."}), 500


@main.route('/api/user/subscription_status', methods=['GET'])
@login_required  # Ensure user is logged in (import from flask_login if needed)
def get_subscription_status():
    return jsonify({
        'event_credits': current_user.event_credits,
        'subscription_expiry_date': current_user.subscription_expiry_date.isoformat() if current_user.subscription_expiry_date else None
    })

@main.route("/api/paypal/webhook", methods=["POST"])
def paypal_webhook():
    """
    Listens for notifications from PayPal about subscription events.
    This is the key to handling automatic renewals.
    """
    webhook_data = request.get_json()
    event_type = webhook_data.get("event_type")
    resource = webhook_data.get("resource", {})

    print(f"--- PayPal Webhook Received: {event_type} ---")

    # The two most important events are:
    # 1. BILLING.SUBSCRIPTION.ACTIVATED: When the subscription starts.
    # 2. PAYMENT.SALE.COMPLETED: For every successful recurring payment.

    if event_type in ["BILLING.SUBSCRIPTION.ACTIVATED", "PAYMENT.SALE.COMPLETED"]:
        subscription_id = resource.get("id")
        if event_type == "PAYMENT.SALE.COMPLETED":
            # For recurring payments, the subscription ID is in a different place
            subscription_id = resource.get("billing_agreement_id")

        # Get the user ID we stored in `custom_id` when creating the subscription
        user_id = resource.get("custom_id")
        if not user_id:
             # If custom_id is not in the top-level resource, we need to fetch the subscription details
            try:
                access_token = get_access_token()
                headers = {"Authorization": f"Bearer {access_token}"}
                sub_details_resp = requests.get(f"{PAYPAL_BASE}/v1/billing/subscriptions/{subscription_id}", headers=headers)
                sub_details_resp.raise_for_status()
                user_id = sub_details_resp.json().get("custom_id")
            except Exception as e:
                print(f"Could not fetch subscription details to find user_id: {e}")
                return jsonify(status="error", reason="could not find user"), 500

        user = User.query.get(user_id)
        if not user:
            print(f"Webhook Error: User with ID {user_id} not found.")
            return jsonify(status="error", reason="user not found"), 404

        # Grant credits and update expiry date
        # If the subscription is already active, this adds 30 days to the current expiry date
        # Otherwise, it sets it to 30 days from now.
        current_expiry = user.subscription_expiry_date or date.today()
        if current_expiry < date.today():
            current_expiry = date.today()

        user.event_credits = (user.event_credits or 0) + 4
        user.subscription_expiry_date = current_expiry + timedelta(days=30)
        user.paypal_subscription_id = subscription_id # Store the subscription ID
        
        db.session.commit()
        
        # Send a confirmation email only on the first activation
        if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            send_subscription_email(user.email)

        print(f"Successfully processed webhook for user {user.email}. Credits: {user.event_credits}, Expiry: {user.subscription_expiry_date}")

    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        subscription_id = resource.get("id")
        # Find the user by their subscription ID and handle cancellation
        # For now, we'll just log it. You could clear their expiry date here if you want.
        user = User.query.filter_by(paypal_subscription_id=subscription_id).first()
        if user:
            # Optionally, you can set their expiry date to now or leave it to run out.
            # user.subscription_expiry_date = date.today()
            # db.session.commit()
            print(f"Subscription {subscription_id} for user {user.email} was cancelled.")
        else:
            print(f"Received cancellation for unknown subscription ID: {subscription_id}")

    return jsonify(status="success"), 200


@main.route("/api/rsvp/credit", methods=['POST'])
@login_required
def rsvp_with_credit():
    data = request.get_json()
    event_id = data.get('event_id')
    user = current_user
    today = date.today()

    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found.'}), 404
    
    current_attendees = EventAttendee.query.filter_by(event_id=event.id).all()
    current_rsvp_count = sum(1 + (a.guest_count or 0) for a in current_attendees)

    # This flow assumes the user is RSVPing for just themselves (1 person).
    if current_rsvp_count + 1 > event.max_capacity:
        return jsonify({'error': 'Sorry, this event is now full.'}), 400


    if not user.has_used_free_event:
        user.has_used_free_event = True
        message = "Your first free event has been successfully claimed!"
        
    elif user.event_credits > 0 and (user.subscription_expiry_date is None or user.subscription_expiry_date >= today):
        user.event_credits -= 1
        message = f"Successfully RSVP'd using one credit! You have {user.event_credits} credits remaining."
        
    else:
        return jsonify({'error': 'No free event or credits available.'}), 400

    # Create the attendee record
    new_attendee = EventAttendee(event_id=event.id, user_id=user.id, guest_count=0)
    db.session.add(new_attendee)
    db.session.commit()
    
    session['flashMessage'] = message # Use session for flash messages
    session['flashEventId'] = event_id
    return jsonify({'success': True, 'message': message}), 200



# Add this new route to your views.py file

@main.route('/events/add_recurring', methods=['POST'])
@login_required # Make sure to import login_required from flask_login
def add_recurring_events():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        # 1. Parse all form data
        form = request.form
        start_date_str = form.get('recurring_start_date')
        end_date_str = form.get('recurring_end_date')
        weekdays = form.getlist('weekdays') # Gets a list of selected weekday values ('0', '1', etc.)

        # Convert strings to proper data types
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        selected_weekdays = [int(day) for day in weekdays]
        
        start_time_obj = datetime.strptime(form.get('start_time'), "%H:%M").time()
        end_time_obj = datetime.strptime(form.get('end_time'), "%H:%M").time()

        # 2. Validate inputs
        if not selected_weekdays:
            return jsonify({'error': 'Please select at least one day of the week.'}), 400
        if start_date > end_date:
            return jsonify({'error': 'Start date cannot be after the end date.'}), 400
        if start_time_obj >= end_time_obj:
            return jsonify({'error': 'Start time must be before end time.'}), 400

        # 3. Calculate all the dates that match the criteria
        dates_to_create = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in selected_weekdays:
                dates_to_create.append(current_date)
            current_date += timedelta(days=1)

        if not dates_to_create:
            return jsonify({'error': 'No matching dates found in the selected range.'}), 400
            
        # --- Handle image upload (same logic as single event) ---
        image_filename = None
        image_file = request.files.get('eventImage')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            save_path = os.path.join(current_app.root_path, 'static/images', unique_filename)
            image_file.save(save_path)
            image_filename = unique_filename
        elif form.get('existingImage'):
            image_filename = form.get('existingImage')


        # 4. Loop through the calculated dates and create events
        for event_date in dates_to_create:
            new_event = Event(
                title=form.get('title'),
                description=form.get('description'),
                start_time=start_time_obj,
                end_time=end_time_obj,
                location=form.get('location'),
                full_address=form.get('full_address'),
                allow_guests=form.get('allow_guests') == 'on',
                guest_limit=int(form.get('guest_limit') or 0),
                ticket_price=float(form.get('ticket_price') or 0.0),
                max_capacity=int(form.get('max_capacity') or 28),
                date=event_date,
                image_filename=image_filename,
                status='active'
            )
            db.session.add(new_event)
        
        # 5. Commit all new events to the database at once
        db.session.commit()

        flash(f'{len(dates_to_create)} recurring events created successfully!', 'success')
        return jsonify({'success': True, 'message': f'{len(dates_to_create)} events were successfully created!'})

    except Exception as e:
        db.session.rollback()
        traceback.print_exc() # Log the full error to your console
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500