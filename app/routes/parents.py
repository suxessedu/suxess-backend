from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user_model import User
from app.models.teacher_profile_model import TeacherProfile
from app.models.request_model import TutorRequest
from app.models.activity_log_model import ActivityLog
from app.utils.subjects import normalize_subject_list
from flask_login import login_required, current_user
from datetime import datetime

parents_bp = Blueprint('parents_bp', __name__)

@parents_bp.route('/request', methods=['POST'])
@login_required
def create_request():
    data = request.get_json()
    parent_id = current_user.id

    new_request = TutorRequest(
        parent_id=parent_id,
        student_name=data.get('studentName'),
        student_age=data.get('studentAge'),
        student_grade=data.get('studentGrade'),
        subjects=data.get('subjects'),
        parent_contact_number=data.get('parentContact'),
        house_address=data.get('houseAddress'),
        schedule=data.get('schedule'),
        duration=data.get('duration'),
        learning_goals=data.get('learningGoals'),
        previous_experience=data.get('previousExperience'),
        teaching_style_preference=data.get('stylePreference')
    )
    db.session.add(new_request)
    db.session.commit()

    log_entry = ActivityLog(user_id=parent_id, action='PARENT_REQUEST_CREATED', details=f"Parent '{current_user.full_name}' created request #{new_request.id} for {new_request.subjects}.")
    db.session.add(log_entry)
    db.session.commit()
    
    all_teachers = User.query \
        .join(TeacherProfile) \
        .filter(User.role == 'teacher', TeacherProfile.is_complete == True, User.id_verification_status == 'Verified') \
        .all()

    requested_subjects = normalize_subject_list(new_request.subjects)
    suggested_teachers = []
    if requested_subjects:
        for teacher in all_teachers:
            teacher_subjects = normalize_subject_list(teacher.profile.relevant_subjects)
            common_subjects = set(requested_subjects).intersection(set(teacher_subjects))
            if common_subjects:
                score = (len(common_subjects) / len(requested_subjects)) * 100
                suggested_teachers.append({'id': teacher.id, 'name': teacher.full_name, 'subjects': ', '.join(teacher_subjects).title(), 'qualification': teacher.profile.highest_qualification, 'experience': teacher.profile.teaching_experience, 'matchScore': round(score)})
    
    suggested_teachers.sort(key=lambda x: x['matchScore'], reverse=True)

    return jsonify({'message': 'Request submitted successfully', 'requestId': new_request.id, 'suggestions': suggested_teachers[:5]}), 201


@parents_bp.route('/request/<int:request_id>/finalize', methods=['POST'])
@login_required
def finalize_request(request_id):
    data = request.get_json()
    tutor_request = TutorRequest.query.get_or_404(request_id)

    if tutor_request.parent_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403

    shortlisted_ids = data.get('selectedTutorIds', [])
    request_details = f"for '{tutor_request.subjects}' (Student: {tutor_request.student_name})"
    
    if shortlisted_ids:
        tutor_request.shortlisted_teacher_ids = ','.join(map(str, shortlisted_ids))
        details_log = f"Parent '{current_user.full_name}' shortlisted tutors with IDs: {tutor_request.shortlisted_teacher_ids} for request #{request_id} {request_details}."
    else:
        details_log = f"Parent '{current_user.full_name}' chose 'Let Suxess Decide' for request #{request_id} {request_details}."
    
    tutor_request.status = 'Confirming Payment'
    
    log_entry = ActivityLog(user_id=current_user.id, action='PARENT_REQUEST_FINALIZED', details=details_log)
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({'message': 'Request finalized and is now awaiting payment confirmation.'}), 200


@parents_bp.route('/requests', methods=['GET'])
@login_required
def get_requests():
    parent_id = current_user.id
    requests = TutorRequest.query.filter_by(parent_id=parent_id).order_by(TutorRequest.created_at.desc()).all()
    
    results = []
    for req in requests:
        days_ago = (datetime.utcnow() - req.created_at).days
        submitted_text = "today" if days_ago == 0 else f"{days_ago} day{'s' if days_ago > 1 else ''} ago"
        results.append({
            'id': req.id,
            'subject': req.subjects,
            'level': req.student_grade,
            'status': req.status,
            'location': req.house_address,
            'submittedTime': submitted_text,
        })
    return jsonify(results), 200