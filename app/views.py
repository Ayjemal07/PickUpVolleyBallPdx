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

from .models import EventAttendee, Subscription
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
PAYPAL_BASE = "https://api-m.paypal.com"
PAYPAL_PLAN_ID_TIER1 = os.getenv("PAYPAL_PLAN_ID_TIER1")
PAYPAL_PLAN_ID_TIER2 = os.getenv("PAYPAL_PLAN_ID_TIER2")

def send_subscription_email(user_email):
    body = """
    Thank you for subscribing to Pick Up Volleyball events, we are excited to have you join and be part of our community! 
    
    You can view and sign up for all events using this link: https://pickupvolleyballpdx.com/events

    Subscriptions will renew every 30 days starting from the time of purchase, with 4 new event credits being issued every cycle. Event credits cannot be used for guests, and any unused credits will not roll over. 
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
        date_str = request.form.get('date')
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
            start_datetime = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
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
            date=datetime.strptime(date_str, "%Y-%m-%d").date(),
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
    user_credits = 0
    can_use_credits = False # Renamed for clarity

    if current_user.is_authenticated:
        user_credits = current_user.event_credits
        if not current_user.has_used_free_event:
            user_has_free_event = True
        
        # CORRECT LOGIC: Can the user USE credits? Check expiry date only.
        valid_sub_for_credits = Subscription.query.filter(
            Subscription.user_id == current_user.id,
            Subscription.expiry_date >= date.today()
        ).first()
        if valid_sub_for_credits:
            can_use_credits = True

    print("PayPal Client ID:", PAYPAL_CLIENT_ID)
    return render_template('events.html', 
                           upcoming_events_data=upcoming_events_data,
                           past_events_data=past_events_data,
                           all_events_for_calendar=all_events_for_calendar,
                           user_role=user_role,
                           user_has_free_event=user_has_free_event,
                           user_event_credits=user_credits,
                           has_active_subscription=can_use_credits,
                           image_files=image_files,
                           is_authenticated=is_authenticated,
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


#event details page
@main.route('/events/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    event.formatted_date = event.date.strftime('%b %d, %Y')
    attendees = EventAttendee.query.filter_by(event_id=event.id).all()
    event.rsvp_count = sum(1 + (a.guest_count or 0) for a in attendees)
    user_id = session.get('user_id') or (current_user.id if current_user.is_authenticated else None)
    is_attending = any(a.user_id == user_id for a in attendees)

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
    can_use_credits = False # Renamed for clarity

    if current_user.is_authenticated:
        user_credits = current_user.event_credits
        if not current_user.has_used_free_event:
            user_has_free_event = True
        
        # CORRECT LOGIC: Can the user USE credits? Check expiry date only.
        valid_sub_for_credits = Subscription.query.filter(
            Subscription.user_id == current_user.id,
            Subscription.expiry_date >= date.today()
        ).first()
        if valid_sub_for_credits:
            can_use_credits = True

    return render_template(
        'event_details.html', 
        event=event, 
        event_data=event_dict, 
        attendees=attendees,
        is_attending=is_attending,
        maps_link=maps_link,
        user_has_free_event=user_has_free_event,
        user_event_credits=user_credits,
        has_active_subscription=can_use_credits, # <-- Pass new variable
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

        # CORRECT LOGIC: Can the user USE credits? Check expiry date only.
        valid_sub_for_credits = Subscription.query.filter(
            Subscription.user_id == user.id,
            Subscription.expiry_date >= date.today()
        ).first()

        if not user.has_used_free_event:
            payable_attendees -= 1
        elif valid_sub_for_credits and user.event_credits > 0: # Check if a valid sub exists
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

            # CORRECT LOGIC: Can the user USE credits? Check expiry date only.
            valid_sub_for_credits = Subscription.query.filter(
                Subscription.user_id == user.id,
                Subscription.expiry_date >= date.today()
            ).first()

            if not user.has_used_free_event:
                user.has_used_free_event = True
            elif valid_sub_for_credits and user.event_credits > 0: # Check if a valid sub exists
                user.event_credits -= 1

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

@main.route('/subscriptions')
def subscriptions():
    today = date.today()
    subscriptions_data = []
    total_monthly_credits = 0
    has_tier_1 = False
    has_tier_2 = False

    if current_user.is_authenticated:
        # Fetch all of the user's subscriptions
        user_subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.tier).all()

        # Determine which active tiers the user has
        active_subs = [sub for sub in user_subscriptions if sub.status == 'active']
        has_tier_1 = any(sub.tier == 1 for sub in active_subs)
        has_tier_2 = any(sub.tier == 2 for sub in active_subs)

        for sub in user_subscriptions:
            subscriptions_data.append({
                'id': sub.id,
                'tier': sub.tier,
                'status': sub.status,
                'credits': sub.credits_per_month,
                'renews_on': sub.expiry_date if sub.status == 'active' else None,
                'expires_on': sub.expiry_date if sub.status == 'canceled' else None,
            })
        
        total_monthly_credits = current_user.event_credits

    return render_template(
        'subscriptions.html',
        is_authenticated=current_user.is_authenticated,
        paypal_client_id=PAYPAL_CLIENT_ID,
        today=today,
        subscriptions=subscriptions_data,
        total_monthly_credits=total_monthly_credits,
        has_tier_1=has_tier_1,
        has_tier_2=has_tier_2
    )


@main.route("/api/paypal/confirm-subscription", methods=["POST"])
@login_required
def confirm_subscription():
    data = request.get_json()
    paypal_sub_id = data.get('subscription_id')

    if not paypal_sub_id:
        return jsonify({'error': 'Subscription ID is missing.'}), 400

    try:
        # Check if this subscription already exists in our DB to prevent duplicates
        existing_sub = Subscription.query.filter_by(paypal_subscription_id=paypal_sub_id).first()
        if existing_sub:
            return jsonify({'success': True, 'message': 'Subscription already confirmed.'}), 200

        # Fetch subscription details from PayPal to get the Plan ID, which tells us the tier
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        sub_details_response = requests.get(f"{PAYPAL_BASE}/v1/billing/subscriptions/{paypal_sub_id}", headers=headers)
        sub_details_response.raise_for_status()
        paypal_sub_data = sub_details_response.json()
        plan_id = paypal_sub_data.get('plan_id')

        # Determine tier and credits from the Plan ID
        if plan_id == PAYPAL_PLAN_ID_TIER1:
            tier = 1
            credits_to_add = 4
        elif plan_id == PAYPAL_PLAN_ID_TIER2:
            tier = 2
            credits_to_add = 8
        else:
            return jsonify({'error': 'Unknown subscription plan from PayPal.'}), 400

        # Create the new subscription record in our database
        new_sub = Subscription(
            user_id=current_user.id,
            paypal_subscription_id=paypal_sub_id,
            tier=tier,
            credits_per_month=credits_to_add,
            status='active',
            expiry_date=date.today() + timedelta(days=30)
        )
        db.session.add(new_sub)

        # Add credits to the user's central balance
        current_user.event_credits += credits_to_add
        
        db.session.commit()
        
        # Send the confirmation email
        send_subscription_email(current_user.email)
        
        flash('Your subscription is now active! Thank you for joining.', 'success')
        return jsonify({'success': True, 'message': 'Subscription activated successfully!'}), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'An internal server error occurred: {str(e)}'}), 500


@main.route('/api/paypal/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    try:
        # 1. Get tier from the frontend request
        request_data = request.get_json()
        tier = request_data.get('tier')

        # 2. Select the correct Plan ID based on the tier
        if tier == '1':
            plan_id = PAYPAL_PLAN_ID_TIER1
        elif tier == '2':
            plan_id = PAYPAL_PLAN_ID_TIER2
        else:
            return jsonify({'error': 'Invalid subscription tier provided.'}), 400
        
        access_token = get_access_token()
        url = f"{PAYPAL_BASE}/v1/billing/subscriptions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        data = {
            "plan_id": plan_id,
            "subscriber": {
                "email_address": current_user.email
            },
            "application_context": {
                "return_url": url_for('main.subscriptions', _external=True),
                "cancel_url": url_for('main.subscriptions', _external=True)
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            subscription = response.json()
            return jsonify({'id': subscription['id']}), 201
        else:
            return jsonify({'error': 'Failed to create subscription'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# In views.py, update the cancel_subscription route

@main.route('/cancel_subscription/<int:subscription_id>', methods=['POST'])
@login_required
def cancel_subscription(subscription_id):
    # Find the subscription in our database
    sub_to_cancel = Subscription.query.get(subscription_id)

    # Security check: ensure the sub belongs to the current user
    if not sub_to_cancel or sub_to_cancel.user_id != current_user.id:
        return jsonify({'error': 'Subscription not found or you do not have permission to cancel it.'}), 404
    
    if sub_to_cancel.status == 'canceled':
        return jsonify({'error': 'This subscription has already been canceled.'}), 400

    try:
        # Cancel the subscription with PayPal
        access_token = get_access_token()
        url = f"{PAYPAL_BASE}/v1/billing/subscriptions/{sub_to_cancel.paypal_subscription_id}/cancel"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(url, headers=headers, json={'reason': 'User requested cancellation'})

        if response.status_code == 204:
            # Update the status in our database
            sub_to_cancel.status = 'canceled'
            db.session.commit()
            flash('Subscription canceled successfully. Your credits remain until the expiry date.', 'success')
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Failed to cancel subscription with PayPal.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/api/user/subscription_status', methods=['GET'])
@login_required  # Ensure user is logged in (import from flask_login if needed)
def get_subscription_status():
    # CORRECT LOGIC: Can the user USE credits? Check expiry date only.
    valid_sub = Subscription.query.filter(
        Subscription.user_id == current_user.id,
        Subscription.expiry_date >= date.today()
    ).first()
    
    return jsonify({
        'event_credits': current_user.event_credits,
        'has_active_subscription': valid_sub is not None
    })


#upgrade subscription:
@main.route('/api/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    data = request.get_json()
    target_tier = data.get('tier')

    if target_tier != '2':
        return jsonify({'error': 'Upgrade path not supported.'}), 400

    try:
        # Step 1: Find the user's active Tier 1 subscription to cancel it.
        old_subscription = Subscription.query.filter_by(
            user_id=current_user.id, 
            tier=1, 
            status='active'
        ).first()

        if not old_subscription:
            return jsonify({'error': 'No active Tier 1 subscription found to upgrade.'}), 404

        # Step 2: Cancel the old subscription in PayPal to stop future billing.
        access_token = get_access_token()
        cancel_url = f"{PAYPAL_BASE}/v1/billing/subscriptions/{old_subscription.paypal_subscription_id}/cancel"
        headers = {"Authorization": f"Bearer {access_token}"}
        cancel_response = requests.post(cancel_url, headers=headers, json={'reason': 'User upgraded to a new plan.'})
        
        # We proceed even if cancellation fails, but we should log it.
        if cancel_response.status_code != 204:
            print(f"Warning: Failed to cancel old PayPal subscription {old_subscription.paypal_subscription_id} during upgrade.")

        # Step 3: Update the old subscription's status in our database.
        old_subscription.status = 'canceled'
        db.session.commit()

        # Step 4: Create a new PayPal subscription for Tier 2.
        # This part is similar to your existing create_subscription route.
        create_url = f"{PAYPAL_BASE}/v1/billing/subscriptions"
        create_data = {
            "plan_id": PAYPAL_PLAN_ID_TIER2, # Explicitly use Tier 2 plan
            "subscriber": {"email_address": current_user.email},
            "application_context": {
                "return_url": url_for('main.subscriptions', _external=True),
                "cancel_url": url_for('main.subscriptions', _external=True)
            }
        }
        create_response = requests.post(create_url, headers=headers, json=create_data)
        create_response.raise_for_status() # Raise an error if this fails
        
        new_paypal_sub = create_response.json()
        return jsonify({'id': new_paypal_sub['id']}), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'An error occurred during the upgrade process: {str(e)}'}), 500


@main.route('/paypal_webhook', methods=['POST'])
def paypal_webhook():
    data = request.get_json()
    event_type = data.get('event_type')
    resource = data.get('resource')

    if not resource or not event_type:
        return jsonify(status="ignored", reason="Missing resource or event_type"), 200

    subscription_id = resource.get('id')
    if not subscription_id:
        return jsonify(status="ignored", reason="Missing subscription ID in resource"), 200

    # Find the subscription in our database, not the user
    subscription = Subscription.query.filter_by(paypal_subscription_id=subscription_id).first()
    if not subscription:
        print(f"Received webhook for unknown subscription ID: {subscription_id}")
        return jsonify(status="ignored"), 200

    user = subscription.user

    if event_type == "BILLING.SUBSCRIPTION.UPDATED" or event_type == "BILLING.SUBSCRIPTION.RE-ACTIVATED":
        # On renewal, add the subscription's credits to the user's balance
        # and push the expiry date forward 30 days.
        user.event_credits += subscription.credits_per_month
        subscription.expiry_date = date.today() + timedelta(days=30)
        subscription.status = 'active' # Ensure status is active on renewal
        db.session.commit()
        print(f"Webhook processed RENEWAL for {user.email}. Credits: {user.event_credits}")

    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        subscription.status = 'canceled'
        db.session.commit()
        print(f"Subscription {subscription_id} for user {user.email} was cancelled via webhook.")
        
    elif event_type == "BILLING.SUBSCRIPTION.EXPIRED" or event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
        subscription.status = 'canceled' # Or another status like 'expired'
        db.session.commit()
        print(f"Subscription {subscription_id} for user {user.email} has expired or been suspended.")

    return jsonify(status="success"), 200


@main.route("/api/rsvp/credit", methods=['POST'])
@login_required
def rsvp_with_credit():
    data = request.get_json()
    event_id = data.get('event_id')
    user = current_user

    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found.'}), 404
    
    current_attendees = EventAttendee.query.filter_by(event_id=event.id).all()
    current_rsvp_count = sum(1 + (a.guest_count or 0) for a in current_attendees)

    # This flow assumes the user is RSVPing for just themselves (1 person).
    if current_rsvp_count + 1 > event.max_capacity:
        return jsonify({'error': 'Sorry, this event is now full.'}), 400
    
    # CORRECT LOGIC: Can the user USE credits? Check expiry date only.
    valid_sub_for_credits = Subscription.query.filter(
        Subscription.user_id == user.id,
        Subscription.expiry_date >= date.today()
    ).first()

    if not user.has_used_free_event:
        user.has_used_free_event = True
        message = "Your first free event has been successfully claimed!"
        
    elif user.event_credits > 0 and valid_sub_for_credits: # Check if a valid sub exists
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


@main.route('/api/rsvp/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_rsvp(event_id):
    user = current_user
    event = Event.query.get_or_404(event_id)

    # Check if the event is in the past
    event_end_datetime = datetime.combine(event.date, event.end_time)
    if event_end_datetime < datetime.now():
        return jsonify({'error': 'Cannot cancel RSVP for an event that has already passed.'}), 400

    # Find the user's RSVP
    rsvp = EventAttendee.query.filter_by(event_id=event.id, user_id=user.id).first()

    if not rsvp:
        return jsonify({'error': 'You are not currently RSVP\'d to this event.'}), 404

    try:
        db.session.delete(rsvp)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Your RSVP has been successfully canceled.'}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    

@main.route('/api/rsvp/update', methods=['POST'])
@login_required
def update_rsvp():
    data = request.get_json()
    event_id = data.get('event_id')
    new_guest_count = data.get('new_guest_count')

    if event_id is None or new_guest_count is None:
        return jsonify({'error': 'Event ID and new guest count are required.'}), 400

    # Find the existing RSVP for the current user and event
    rsvp = EventAttendee.query.filter_by(event_id=event_id, user_id=current_user.id).first()

    if not rsvp:
        return jsonify({'error': 'No existing RSVP found to update.'}), 404

    try:
        rsvp.guest_count = int(new_guest_count)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Your RSVP has been successfully updated!'
        }), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

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