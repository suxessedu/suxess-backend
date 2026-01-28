from app.extensions import db
import datetime

class TutorRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # NEW FIELD: Store parent's choices as a comma-separated string of teacher IDs
    shortlisted_teacher_ids = db.Column(db.String(255), nullable=True)
    
    student_name = db.Column(db.String(100), nullable=False)
    student_age = db.Column(db.String(20))
    student_grade = db.Column(db.String(50), nullable=False)
    subjects = db.Column(db.String(255), nullable=False)
    
    parent_contact_number = db.Column(db.String(50))
    house_address = db.Column(db.String(255), nullable=False)
    
    schedule = db.Column(db.String(255))
    duration = db.Column(db.String(100))
    learning_goals = db.Column(db.Text)
    
    previous_experience = db.Column(db.String(10))
    teaching_style_preference = db.Column(db.Text)
    
    status = db.Column(db.String(20), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    parent = db.relationship('User', foreign_keys=[parent_id], backref='requests_made')
    assigned_teacher = db.relationship('User', foreign_keys=[assigned_teacher_id], backref='assignments')