from app.extensions import db
import datetime

class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('tutor_request.id'), nullable=False)
    lesson_date = db.Column(db.Date, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    teacher_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Confirmed, Disputed
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    teacher = db.relationship('User', backref='lesson_logs')
    request = db.relationship('TutorRequest', backref='lesson_logs')