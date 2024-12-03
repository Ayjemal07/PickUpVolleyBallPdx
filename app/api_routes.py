from flask import Blueprint, jsonify
from .models import Event

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([
        {
            "id": event.id,
            "title": event.name,
            "start": event.date_time.isoformat(),
            "description": event.description,
        }
        for event in events
    ])
