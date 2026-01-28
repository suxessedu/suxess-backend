from app.extensions import db

class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    highest_qualification = db.Column(db.String(100))
    relevant_subjects = db.Column(db.Text)
    teaching_experience = db.Column(db.Text)
    
    teaching_philosophy = db.Column(db.Text)
    lesson_planning = db.Column(db.Text)
    specialized_methods = db.Column(db.Text)
    
    home_address = db.Column(db.String(255))
    guarantor_name = db.Column(db.String(100))
    guarantor_address = db.Column(db.String(255))
    
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    
    # THE CRITICAL FIX: This line creates the link that `current_user.profile` needs.
    user = db.relationship('User', backref=db.backref('profile', uselist=False, lazy=True))