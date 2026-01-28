from flask import Blueprint, jsonify
from app.extensions import db
from app.models.request_model import TutorRequest
from flask_login import login_required, current_user

requests_bp = Blueprint('requests_bp', __name__)

@requests_bp.route('/<int:request_id>', methods=['GET'])
@login_required
def get_request_details(request_id):
    tutor_request = TutorRequest.query.get_or_404(request_id)

    is_parent_of_request = current_user.id == tutor_request.parent_id
    is_assigned_teacher = current_user.id == tutor_request.assigned_teacher_id
    is_teacher_browsing_pending = current_user.role == 'teacher' and tutor_request.status == 'Pending'

    if not (is_parent_of_request or is_assigned_teacher or is_teacher_browsing_pending):
        return jsonify(message="Unauthorized"), 403

    details = {
        'id': tutor_request.id, 'status': tutor_request.status, 'studentName': tutor_request.student_name,
        'studentAge': tutor_request.student_age, 'studentGrade': tutor_request.student_grade,
        'subjects': tutor_request.subjects, 'schedule': tutor_request.schedule, 'duration': tutor_request.duration,
        'learningGoals': tutor_request.learning_goals, 'location': tutor_request.house_address,
        'previousExperience': tutor_request.previous_experience, 'stylePreference': tutor_request.teaching_style_preference,
        'createdAt': tutor_request.created_at.strftime('%Y-%m-%d %H:%M'),
        'parentName': tutor_request.parent.full_name,
    }

    if is_assigned_teacher:
        details['parentContact'] = tutor_request.parent_contact_number
    elif current_user.role == 'teacher':
        details['parentContact'] = 'Revealed after match'
    else: 
        details['parentContact'] = tutor_request.parent_contact_number

    if tutor_request.assigned_teacher:
        details['assignedTeacher'] = {
            'name': tutor_request.assigned_teacher.full_name,
            'email': tutor_request.assigned_teacher.email,
            'phone': tutor_request.assigned_teacher.phone_number,
            'qualification': tutor_request.assigned_teacher.profile.highest_qualification if tutor_request.assigned_teacher.profile else 'N/A'
        }

    return jsonify(details), 200


@requests_bp.route('/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    tutor_request = TutorRequest.query.get_or_404(request_id)

    if current_user.id != tutor_request.parent_id:
        return jsonify(message="Unauthorized"), 403
    if tutor_request.status != 'Pending':
        return jsonify(message="Only pending requests can be cancelled"), 400
    
    tutor_request.status = 'Cancelled'
    db.session.commit()
    
    return jsonify(message="Request cancelled successfully"), 200