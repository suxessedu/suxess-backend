from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.user_model import User
from app.models.request_model import TutorRequest
from app.models.notification_model import Notification
from flask_login import login_required, current_user
from app.utils.crypto import encrypt_data
from sqlalchemy import func
from datetime import datetime
from app.extensions import mail
from flask_mail import Message
import os

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/submit-verification', methods=['POST'])
@login_required
def submit_verification():
    data = request.get_json()
    phone_number = data.get('phoneNumber')
    nin = data.get('nin')

    if not phone_number or not nin:
        return jsonify({'message': 'Phone number and NIN are required.'}), 400

    user = User.query.get(current_user.id)
    user.phone_number = phone_number
    user.nin = encrypt_data(nin) # Encrypt the NIN before saving
    user.id_verification_status = 'Pending'
    db.session.commit()

    return jsonify({'message': 'Verification submitted for review.'}), 200


@users_bp.route('/dashboard-summary', methods=['GET'])
@login_required
def dashboard_summary():
    user_id = current_user.id

    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    if current_user.role == 'parent':
        active_requests = db.session.query(func.count(TutorRequest.id)).filter(TutorRequest.parent_id == user_id, TutorRequest.status == 'Pending').scalar()
        matched_tutors = db.session.query(func.count(TutorRequest.id)).filter(TutorRequest.parent_id == user_id, TutorRequest.status == 'Matched').scalar()
        completed = db.session.query(func.count(TutorRequest.id)).filter(TutorRequest.parent_id == user_id, TutorRequest.status == 'Completed').scalar()
        
        latest_request = TutorRequest.query.filter_by(parent_id=user_id).order_by(TutorRequest.created_at.desc()).first()
        latest_request_data = None
        if latest_request:
            days_ago = (datetime.utcnow() - latest_request.created_at).days
            submitted_text = "Submitted today" if days_ago == 0 else f"Submitted {days_ago} day{'s' if days_ago > 1 else ''} ago"
            latest_request_data = { 'id': latest_request.id, 'subject': latest_request.subjects, 'level': latest_request.student_grade, 'status': latest_request.status, 'submittedTime': submitted_text }

        return jsonify({
            'kpis': [{'label': 'Active Requests', 'value': active_requests}, {'label': 'Matched Tutors', 'value': matched_tutors}, {'label': 'Completed', 'value': completed}],
            'latestItem': latest_request_data,
            'unreadCount': unread_count
        }), 200

    elif current_user.role == 'teacher':
        available = db.session.query(func.count(TutorRequest.id)).filter(TutorRequest.status == 'Pending').scalar()
        assigned = db.session.query(func.count(TutorRequest.id)).filter(TutorRequest.assigned_teacher_id == user_id, TutorRequest.status.in_(['Matched', 'Pending Acceptance'])).scalar()
        completed = db.session.query(func.count(TutorRequest.id)).filter(TutorRequest.assigned_teacher_id == user_id, TutorRequest.status == 'Completed').scalar()

        latest_assignment = TutorRequest.query.filter(TutorRequest.assigned_teacher_id == user_id, TutorRequest.status.in_(['Matched', 'Pending Acceptance'])).order_by(TutorRequest.created_at.desc()).first()
        latest_assignment_data = None
        if latest_assignment:
            latest_assignment_data = { 'id': latest_assignment.id, 'subject': latest_assignment.subjects, 'level': f"{latest_assignment.student_grade} - {latest_assignment.parent.full_name.split(' ')[0]}'s Child", 'status': latest_assignment.status, 'schedule': latest_assignment.schedule }

        return jsonify({
            'kpis': [{'label': 'New Requests', 'value': available}, {'label': 'Your Students', 'value': assigned}, {'label': 'Sessions', 'value': completed}],
            'latestItem': latest_assignment_data,
            'unreadCount': unread_count
        }), 200

    return jsonify({'message': 'Invalid role'}), 400

@users_bp.route('/contact-admin', methods=['POST'])
@login_required
def contact_admin():
    data = request.get_json()
    message_body = data.get('message')

    if not message_body:
        return jsonify(message="Message cannot be empty."), 400

    admin_email = os.environ.get('SUPER_ADMIN_EMAIL')
    msg = Message(
        subject=f"New Message from Suxess User: {current_user.full_name}",
        recipients=[admin_email],
        body=f"User: {current_user.full_name} ({current_user.email})\nRole: {current_user.role}\n\nMessage:\n{message_body}"
    )
    mail.send(msg)

    return jsonify(message="Your message has been sent to the admin team."), 200


@users_bp.route('/register-push-token', methods=['POST'])
@login_required
def register_push_token():
    data = request.get_json()
    token = data.get('token')
    
    user = User.query.get(current_user.id)
    user.push_token = token
    db.session.commit()
    
    return jsonify(message="Token registered successfully"), 200