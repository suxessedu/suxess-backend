from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.news_model import News
from app.models.user_model import User
from flask_login import login_required, current_user
from datetime import datetime
from app.services.push_service import send_push_notification

news_bp = Blueprint('news_bp', __name__)

@news_bp.route('/', methods=['GET'])
@login_required
def get_news():
    role = current_user.role
    
    query = News.query.filter_by(is_published=True)
    
    if role == 'parent':
        query = query.filter((News.target_role == 'all') | (News.target_role == 'parent'))
    elif role == 'teacher':
        query = query.filter((News.target_role == 'all') | (News.target_role == 'teacher'))
    # Admins see everything, so no filter needed for them if they call this endpoint, 
    # but practically admins might want to see 'all' published news too.
    
    news_list = query.order_by(News.created_at.desc()).all()
    
    return jsonify([news.to_dict() for news in news_list]), 200

@news_bp.route('/<int:news_id>', methods=['GET'])
@login_required
def get_single_news(news_id):
    news = News.query.get_or_404(news_id)
    # Basic permission check: if not admin, ensure role matches
    if current_user.role != 'admin':
        if news.target_role != 'all' and news.target_role != current_user.role:
             return jsonify(message="You do not have permission to view this news."), 403

    return jsonify(news.to_dict()), 200

# --- Admin Routes ---

@news_bp.route('/', methods=['POST'])
@login_required
def create_news():
    if current_user.role != 'admin':
        return jsonify(message="Unauthorized"), 403
        
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    target_role = data.get('targetRole', 'all')
    send_push = data.get('sendPush', False)
    
    if not title or not content:
        return jsonify(message="Title and Content are required"), 400
        
    new_news = News(
        title=title,
        content=content,
        target_role=target_role,
        author_id=current_user.id
    )
    
    db.session.add(new_news)
    db.session.commit()
    
    # Send Push Notification Logic
    if send_push:
        # Retrieve tokens based on target_role
        query = User.query.filter(User.push_token.isnot(None))
        if target_role and target_role != 'all':
            query = query.filter(User.role == target_role)
            
        users = query.all()
        tokens = [u.push_token for u in users if u.push_token]
        if tokens:
            try:
                from app.services.push_service import send_push_notifications
                send_push_notifications(
                    tokens=tokens,
                    title=f"📢 Suxess Update: {title}",
                    body="Tap to read the latest announcement.",
                    data={'newsId': new_news.id}
                )
            except Exception as e:
                print(f"Error broadcasting news push: {e}")

    return jsonify(new_news.to_dict()), 201

@news_bp.route('/<int:news_id>', methods=['DELETE'])
@login_required
def delete_news(news_id):
    if current_user.role != 'admin':
        return jsonify(message="Unauthorized"), 403
        
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    
    return jsonify(message="News deleted successfully"), 200
