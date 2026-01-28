from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.notification_model import Notification
from flask_login import login_required, current_user

notifications_bp = Blueprint('notifications', __name__)

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
