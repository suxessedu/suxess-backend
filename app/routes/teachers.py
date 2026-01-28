from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.teacher_profile_model import TeacherProfile
from app.models.request_model import TutorRequest
from app.models.lesson_log_model import LessonLog
from app.models.notification_model import Notification
from flask_login import login_required, current_user
from datetime import datetime

teachers_bp = Blueprint('teachers_bp', __name__)

@teachers_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    profile = current_user.profile
    if not profile:
        return jsonify({'message': 'Profile not found for this teacher'}), 404
    
    data = request.get_json()
    profile.highest_qualification = data.get('highestQualification')
    profile.relevant_subjects = data.get('relevantSubjects')
    profile.teaching_experience = data.get('teachingExperience')
    profile.teaching_philosophy = data.get('teachingPhilosophy')
    profile.lesson_planning = data.get('lessonPlanning')
    profile.specialized_methods = data.get('specializedMethods')
    profile.home_address = data.get('homeAddress')
    profile.guarantor_name = data.get('guarantorName')
    profile.guarantor_address = data.get('guarantorAddress')
    profile.is_complete = True
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

@teachers_bp.route('/assignments', methods=['GET'])
@login_required
def get_assignments():
    teacher_id = current_user.id
    assignments = TutorRequest.query.filter_by(assigned_teacher_id=teacher_id).order_by(TutorRequest.created_at.desc()).all()
    
    results = []
    for req in assignments:
        days_ago = (datetime.utcnow() - req.created_at).days
        submitted_text = "Assigned today" if days_ago == 0 else f"Assigned {days_ago} day{'s' if days_ago > 1 else ''} ago"
        results.append({
            'id': req.id,
            'subject': req.subjects,
            'level': f"{req.student_grade} - {req.parent.full_name.split(' ')[0]}'s Child",
            'status': req.status,
            'location': req.house_address,
            'submittedTime': submitted_text,
        })
    return jsonify(results), 200

@teachers_bp.route('/browse-requests', methods=['GET'])
@login_required
def browse_requests():
    # Find all requests that are pending and not made by the current user (if they are also a parent)
    requests = TutorRequest.query.filter_by(status='Pending').filter(TutorRequest.parent_id != current_user.id).order_by(TutorRequest.created_at.desc()).all()
    results = [{'id': req.id, 'subject': req.subjects, 'level': req.student_grade, 'location': req.house_address, 'schedule': req.schedule} for req in requests]
    return jsonify(results), 200

@teachers_bp.route('/log-lesson', methods=['POST'])
@login_required
def log_lesson():
    if current_user.role != 'teacher':
        return jsonify(message="Only teachers can log lessons"), 403

    data = request.get_json()
    request_id = data.get('requestId')
    lesson_date = data.get('lessonDate')
    duration_hours = data.get('durationHours')
    teacher_notes = data.get('teacherNotes')

    if not all([request_id, lesson_date, duration_hours]):
        return jsonify(message="Missing required fields"), 400
    
    # Verify this teacher is assigned to this request
    tutor_request = TutorRequest.query.get_or_404(request_id)
    if tutor_request.assigned_teacher_id != current_user.id:
        return jsonify(message="You are not assigned to this request"), 403

    new_log = LessonLog(
        teacher_id=current_user.id,
        request_id=request_id,
        lesson_date=datetime.strptime(lesson_date, '%Y-%m-%d').date(),
        duration_hours=float(duration_hours),
        teacher_notes=teacher_notes
    )
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify(message="Lesson logged successfully"), 201

@teachers_bp.route('/assignments/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_assignment(request_id):
    if current_user.role != 'teacher':
        return jsonify(message="Only teachers can accept assignments"), 403

    tutor_request = TutorRequest.query.get_or_404(request_id)
    if tutor_request.assigned_teacher_id != current_user.id:
        return jsonify(message="You are not assigned to this request"), 403
    
    if tutor_request.status != 'Pending Acceptance':
        return jsonify(message="This request is not pending acceptance"), 400

    tutor_request.status = 'Matched'
    db.session.commit()
    
    # Notify Parent
    notif_parent = Notification(user_id=tutor_request.parent_id, title="Tutor Accepted!", message=f"The tutor {current_user.full_name} has accepted your request! You can now connect.", type="success")
    db.session.add(notif_parent)
    db.session.commit()

    return jsonify(message="Assignment accepted successfully"), 200

@teachers_bp.route('/assignments/<int:request_id>/decline', methods=['POST'])
@login_required
def decline_assignment(request_id):
    if current_user.role != 'teacher':
        return jsonify(message="Only teachers can decline assignments"), 403

    tutor_request = TutorRequest.query.get_or_404(request_id)
    if tutor_request.assigned_teacher_id != current_user.id:
        return jsonify(message="You are not assigned to this request"), 403

    # Reset the request
    tutor_request.assigned_teacher_id = None
    tutor_request.status = 'Pending'
    db.session.commit()
    
    return jsonify(message="Assignment declined successfully"), 200