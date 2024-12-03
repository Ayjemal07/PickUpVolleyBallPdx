from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from . import db
from .models import Event
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/events', methods=['GET', 'POST'])
@login_required
def manage_events():
    if request.method == 'POST':
        # Create Event
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        date_time = datetime.strptime(request.form['date_time'], '%Y-%m-%d %H:%M')
        new_event = Event(name=name, description=description, location=location, date_time=date_time)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('admin.manage_events'))
    
    events = Event.query.all()
    return render_template('admin/manage_events.html', events=events)

@admin_bp.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('admin.manage_events'))

@admin_bp.route('/event/<int:event_id>/publish', methods=['POST'])
@login_required
def publish_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = 'published'
    db.session.commit()
    return redirect(url_for('admin.manage_events'))
