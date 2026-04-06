from app.extensions import db
from datetime import datetime

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False) # HTML Content
    target_role = db.Column(db.String(50), default='all') # all, parent, teacher
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('news_posts', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'targetRole': self.target_role,
            'authorName': self.author.full_name if self.author else 'Unknown',
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'isPublished': self.is_published
        }
