from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.message_model import Message
from app.models.request_model import TutorRequest
from flask_login import login_required, current_user

messages_bp = Blueprint('messages_bp', __name__)

@messages_bp.route('/<int:request_id>', methods=['GET'])
@login_required
def get_messages(request_id):
    tutor_request = TutorRequest.query.get_or_404(request_id)
    if current_user.id not in [tutor_request.parent_id, tutor_request.assigned_teacher_id]:
        return jsonify(message="Unauthorized"), 403

    messages = Message.query.filter_by(request_id=request_id).order_by(Message.timestamp.asc()).all()
    result = [{
        'id': msg.id,
        'senderId': msg.sender_id,
        'body': msg.body,
        'timestamp': msg.timestamp.isoformat() + 'Z'
    } for msg in messages]
    return jsonify(result), 200

@messages_bp.route('/<int:request_id>', methods=['POST'])
@login_required
def send_message(request_id):
    data = request.get_json()
    body = data.get('body')
    if not body:
        return jsonify(message="Message body cannot be empty"), 400

    tutor_request = TutorRequest.query.get_or_404(request_id)
    if current_user.id not in [tutor_request.parent_id, tutor_request.assigned_teacher_id]:
        return jsonify(message="Unauthorized"), 403

    recipient_id = tutor_request.assigned_teacher_id if current_user.id == tutor_request.parent_id else tutor_request.parent_id
    
    new_message = Message(
        request_id=request_id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        body=body
    )
    db.session.add(new_message)
    db.session.commit()
    
    # We could trigger a push notification to the recipient here
    
    return jsonify(message="Message sent"), 201