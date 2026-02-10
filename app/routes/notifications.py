from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.notification_model import Notification
from app.models.user_model import User
from app.services.push_service import send_push_notifications
from flask_login import login_required, current_user

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/register-token', methods=['POST'])
@login_required
def register_token():
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'message': 'Token is required'}), 400
        
    current_user.push_token = token
    db.session.commit()
    
    return jsonify({'message': 'Token registered successfully'}), 200

@notifications_bp.route('/broadcast', methods=['POST'])
@login_required
def broadcast_notification():
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    title = data.get('title')
    message = data.get('message')
    target_role = data.get('targetRole') # 'all', 'parent', 'teacher'
    
    if not title or not message:
        return jsonify({'message': 'Title and message are required'}), 400
        
    # Build query
    query = User.query
    if target_role and target_role != 'all':
        query = query.filter_by(role=target_role)
    
    users = query.all()
    
    # improved: Collect tokens and create DB notifications in bulk/loop
    tokens = []
    for user in users:
        # Create In-App Notification
        notif = Notification(
            user_id=user.id,
            title=title,
            message=message,
            type='info'
        )
        db.session.add(notif)
        
        if user.push_token:
            tokens.append(user.push_token)
            
    db.session.commit()
    
    # Send Push
    if tokens:
        send_push_notifications(tokens, title, message)
    
    return jsonify({'message': f'Broadcast sent to {len(users)} users'}), 200

@notifications_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    result = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'isRead': n.is_read,
        'createdAt': n.created_at.strftime('%Y-%m-%d %H:%M')
    } for n in notifications]
    
    return jsonify(result), 200

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Marked as read'}), 200
    
@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All marked as read'}), 200
