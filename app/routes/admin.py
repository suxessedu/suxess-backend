import requests
from flask import Blueprint, jsonify, request
from app.extensions import db, mail
from app.models.user_model import User
from app.models.teacher_profile_model import TeacherProfile
from app.models.request_model import TutorRequest
from app.models.activity_log_model import ActivityLog
from app.models.lesson_log_model import LessonLog
from app.models.notification_model import Notification
from app.utils.subjects import normalize_subject_list
from app.utils.crypto import decrypt_data
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from flask_mail import Message


admin_bp = Blueprint('admin_bp', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify(message="Admins only!"), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    total_parents = db.session.query(func.count(User.id)).filter_by(role='parent').scalar()
    total_teachers = db.session.query(func.count(User.id)).filter_by(role='teacher').scalar()
    pending_requests = db.session.query(func.count(TutorRequest.id)).filter_by(status='Pending').scalar()
    matched_requests = db.session.query(func.count(TutorRequest.id)).filter_by(status='Matched').scalar()
    return jsonify({'parents': total_parents, 'teachers': total_teachers, 'pending': pending_requests, 'matched': matched_requests}), 200

@admin_bp.route('/activity-logs', methods=['GET'])
@admin_required
def get_activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(5).all()
    result = [{'id': log.id, 'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'userName': log.user.full_name if log.user else 'System', 'action': log.action, 'details': log.details} for log in logs]
    return jsonify(result), 200
    
@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_all_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = ActivityLog.query
    if start_date: query = query.filter(ActivityLog.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(ActivityLog.timestamp < end_date_obj)
    pagination = query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    result = {'logs': [{'id': log.id, 'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'userName': log.user.full_name if log.user else 'System', 'action': log.action, 'details': log.details} for log in logs], 'total': pagination.total, 'pages': pagination.pages, 'current_page': pagination.page}
    return jsonify(result), 200

@admin_bp.route('/requests', methods=['GET'])
@admin_required
def get_all_requests():
    requests = TutorRequest.query.order_by(TutorRequest.created_at.desc()).all()
    result = [{'id': req.id, 'parentName': req.parent.full_name, 'parentEmail': req.parent.email, 'studentName': req.student_name, 'studentGrade': req.student_grade, 'subjects': req.subjects, 'status': req.status, 'createdAt': req.created_at.strftime('%Y-%m-%d %H:%M'), 'location': req.house_address, 'schedule': req.schedule, 'duration': req.duration, 'learningGoals': req.learning_goals, 'assignedTeacherId': req.assigned_teacher_id, 'assignedTeacherName': req.assigned_teacher.full_name if req.assigned_teacher else None} for req in requests]
    return jsonify(result), 200

@admin_bp.route('/teachers', methods=['GET'])
@admin_required
def get_all_teachers():
    teachers = User.query.filter_by(role='teacher').join(User.profile, isouter=True).order_by(User.full_name).all()
    result = []
    for teacher in teachers:
        assigned_count = db.session.query(func.count(TutorRequest.id)).filter_by(assigned_teacher_id=teacher.id, status='Matched').scalar()
        completed_count = db.session.query(func.count(TutorRequest.id)).filter_by(assigned_teacher_id=teacher.id, status='Completed').scalar()
        result.append({
            'id': teacher.id,
            'name': teacher.full_name,
            'email': teacher.email,
            'phone': teacher.phone_number,
            'nin': decrypt_data(teacher.nin),
            'subjects': teacher.profile.relevant_subjects if teacher.profile else 'N/A',
            'isProfileComplete': teacher.profile.is_complete if teacher.profile else False,
            'verificationStatus': teacher.id_verification_status,
            'isSuspended': teacher.is_suspended,
            'assignedCount': assigned_count,
            'completedCount': completed_count,
        })
    return jsonify(result), 200

@admin_bp.route('/parents', methods=['GET'])
@admin_required
def get_all_parents():
    parents = User.query.filter_by(role='parent').order_by(User.full_name).all()
    result = []
    for parent in parents:
        request_count = db.session.query(func.count(TutorRequest.id)).filter_by(parent_id=parent.id).scalar()
        result.append({
            'id': parent.id,
            'name': parent.full_name,
            'email': parent.email,
            'phone': parent.phone_number,
            'verificationStatus': parent.id_verification_status,
            'requestCount': request_count,
            'isPremium': parent.is_premium, # Add premium status
        })
    return jsonify(result), 200

@admin_bp.route('/parents/<int:parent_id>', methods=['GET'])
@admin_required
def get_parent_details(parent_id):
    parent = User.query.get_or_404(parent_id)
    if parent.role != 'parent':
        return jsonify({'message': 'User is not a parent'}), 404
    
    return jsonify({
        'id': parent.id,
        'name': parent.full_name,
        'email': parent.email,
        'phone': parent.phone_number,
        'nin': decrypt_data(parent.nin),
        'verificationStatus': parent.id_verification_status,
    }), 200


@admin_bp.route('/requests/<int:request_id>/suggest-teachers', methods=['GET'])
@admin_required
def suggest_teachers(request_id):
    tutor_request = TutorRequest.query.get_or_404(request_id)
    shortlisted_ids_str = tutor_request.shortlisted_teacher_ids
    if shortlisted_ids_str:
        shortlisted_ids = [int(id_str) for id_str in shortlisted_ids_str.split(',')]
        teachers_query = User.query.filter(User.id.in_(shortlisted_ids))
        all_teachers = teachers_query.all()
        suggested_teachers = [{'id': t.id, 'name': t.full_name, 'subjects': t.profile.relevant_subjects if t.profile else 'N/A', 'isShortlisted': True} for t in all_teachers]
    else:
        requested_subjects = normalize_subject_list(tutor_request.subjects)
        if not requested_subjects: return jsonify([]), 200
        all_teachers_with_profiles = User.query.join(TeacherProfile).filter(User.role == 'teacher', TeacherProfile.is_complete == True, User.id_verification_status == 'Verified').all()
        suggested_teachers = []
        for teacher in all_teachers_with_profiles:
            teacher_subjects = normalize_subject_list(teacher.profile.relevant_subjects)
            common_subjects = set(requested_subjects).intersection(set(teacher_subjects))
            if common_subjects:
                score = (len(common_subjects) / len(requested_subjects)) * 100
                suggested_teachers.append({'id': teacher.id, 'name': teacher.full_name, 'subjects': ', '.join(teacher_subjects).title(), 'matchScore': round(score), 'isShortlisted': False})
        suggested_teachers.sort(key=lambda x: x['matchScore'], reverse=True)
    return jsonify(suggested_teachers), 200

@admin_bp.route('/match', methods=['POST'])
@admin_required
def match_tutor():
    data = request.get_json()
    request_id = data.get('requestId')
    teacher_id = data.get('teacherId')

    tutor_request = TutorRequest.query.get(request_id)
    teacher = User.query.get(teacher_id)
    parent = User.query.get(tutor_request.parent_id)

    if not all([tutor_request, teacher, parent]) or teacher.role != 'teacher':
        return jsonify(message="Invalid request, teacher, or parent ID"), 404
    
    tutor_request.assigned_teacher_id = teacher_id
    tutor_request.status = 'Pending Acceptance'
    
    request_details = f"for '{tutor_request.subjects}' (Student: {tutor_request.student_name})"
    log_entry = ActivityLog(user_id=current_user.id, action='ADMIN_OFFERED_TUTOR', details=f"Admin offered Teacher '{teacher.full_name}' to Request #{request_id} {request_details}.")
    db.session.add(log_entry)
    db.session.commit()

    # --- THE DEFINITIVE FIX: EMAIL NOTIFICATION LOGIC ---
    try:
        # Email to Parent
        msg_parent = Message(
            subject="You've been matched with a Suxess Tutor!",
            recipients=[parent.email],
            body=f"Dear {parent.full_name},\n\n"
                 f"We are pleased to inform you that a tutor has been assigned for your request for {tutor_request.subjects}.\n\n"
                 f"Tutor's Name: {teacher.full_name}\n"
                 f"Please log in to the Suxess app to view details and begin communication.\n\n"
                 "Thank you,\nThe Suxess Team"
        )
        mail.send(msg_parent)

        # Email to Teacher
        msg_teacher = Message(
            subject="New Suxess Tutor Assignment!",
            recipients=[teacher.email],
            body=f"Dear {teacher.full_name},\n\n"
                 f"You have been assigned to a new tutoring request from {parent.full_name} for the subject: {tutor_request.subjects}.\n\n"
                 f"Please log in to the Suxess app to view the full request details and connect with the parent.\n\n"
                 "Thank you,\nThe Suxess Team"
        )
        mail.send(msg_teacher)
    except Exception as e:
        print(f"Failed to send match notification emails: {e}")

    # Create In-App Notifications
    notif_parent = Notification(user_id=parent.id, title="Tutor Matched!", message=f"A tutor has been assigned for your request for {tutor_request.subjects}. Check it out now!", type="match")
    notif_teacher = Notification(user_id=teacher.id, title="New Job Offer!", message=f"You have been offered a new tutoring request for {tutor_request.subjects}. Please accept or decline.", type="match")
    db.session.add(notif_parent)
    db.session.add(notif_teacher)
    db.session.commit()

    return jsonify(message=f"Successfully matched {teacher.full_name} to request #{request_id}"), 200

@admin_bp.route('/requests/<int:request_id>/confirm-payment', methods=['POST'])
@admin_required
def confirm_payment(request_id):
    tutor_request = TutorRequest.query.get_or_404(request_id)
    if tutor_request.status != 'Confirming Payment': return jsonify({'message': 'This request is not awaiting payment confirmation.'}), 400
    tutor_request.status = 'Pending'
    request_details = f"for '{tutor_request.subjects}' (Student: {tutor_request.student_name})"
    log_entry = ActivityLog(user_id=current_user.id, action='ADMIN_CONFIRMED_PAYMENT', details=f"Admin confirmed payment for Request #{request_id} {request_details}.")
    db.session.add(log_entry)
    
    # Create In-App Notification
    notif_parent = Notification(user_id=tutor_request.parent_id, title="Payment Confirmed", message=f"Payment for your request for {tutor_request.subjects} has been confirmed. We are now matching you with a tutor.", type="success")
    db.session.add(notif_parent)
    
    db.session.commit()
    return jsonify({'message': 'Payment confirmed. Request is now pending a match.'}), 200
    
@admin_bp.route('/recent-requests', methods=['GET'])
@admin_required
def get_recent_requests():
    requests = TutorRequest.query.order_by(TutorRequest.created_at.desc()).limit(5).all()
    result = [{'id': req.id, 'parentName': req.parent.full_name, 'subjects': req.subjects, 'status': req.status} for req in requests]
    return jsonify(result), 200

@admin_bp.route('/recent-teachers', methods=['GET'])
@admin_required
def get_recent_teachers():
    teachers = User.query.filter_by(role='teacher').order_by(User.id.desc()).limit(5).all()
    result = [{'id': teacher.id, 'name': teacher.full_name, 'email': teacher.email, 'isProfileComplete': teacher.profile.is_complete if teacher.profile else False} for teacher in teachers]
    return jsonify(result), 200

@admin_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@admin_required
def verify_user(user_id):
    user_to_verify = User.query.get_or_404(user_id)
    user_to_verify.id_verification_status = 'Verified'
    db.session.commit()
    return jsonify({'message': f'User {user_to_verify.full_name} has been verified.'}), 200

@admin_bp.route('/chart-data', methods=['GET'])
@admin_required
def get_chart_data():
    today = datetime.utcnow()
    labels = []
    data = []
    for i in range(5, -1, -1):
        target_month_date = today - timedelta(days=i * 30)
        month_name = target_month_date.strftime('%b')
        labels.append(month_name)
        count = db.session.query(func.count(TutorRequest.id)).filter(extract('year', TutorRequest.created_at) == target_month_date.year, extract('month', TutorRequest.created_at) == target_month_date.month).scalar()
        data.append(count)
    return jsonify({'labels': labels, 'data': data}), 200

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
def get_analytics():
    top_subjects_query = db.session.query(TutorRequest.subjects, func.count(TutorRequest.id).label('count')).group_by(TutorRequest.subjects).order_by(func.count(TutorRequest.id).desc()).limit(5).all()
    top_subjects = [{'subject': s[0], 'count': s[1]} for s in top_subjects_query]
    top_teachers_query = db.session.query(User.full_name, func.count(TutorRequest.id).label('count')).join(TutorRequest, User.id == TutorRequest.assigned_teacher_id).group_by(User.full_name).order_by(func.count(TutorRequest.id).desc()).limit(5).all()
    top_teachers = [{'name': t[0], 'count': t[1]} for t in top_teachers_query]
    return jsonify({'topSubjects': top_subjects, 'topTeachers': top_teachers}), 200


@admin_bp.route('/users/<int:user_id>/upgrade-premium', methods=['POST'])
@admin_required
def upgrade_to_premium(user_id):
    user_to_upgrade = User.query.get_or_404(user_id)
    if user_to_upgrade.role != 'parent':
        return jsonify({'message': 'Only parents can be upgraded to premium.'}), 400
    
    user_to_upgrade.is_premium = True
    log_entry = ActivityLog(user_id=current_user.id, action='ADMIN_UPGRADED_PARENT', details=f"Admin upgraded Parent '{user_to_upgrade.full_name}' to Premium.")
    db.session.add(log_entry)
    db.session.commit()
    return jsonify({'message': f'User {user_to_upgrade.full_name} has been upgraded to Premium.'}), 200


@admin_bp.route('/users/<int:user_id>/toggle-suspend', methods=['POST'])
@admin_required
def toggle_suspend_user(user_id):
    user_to_toggle = User.query.get_or_404(user_id)
    user_to_toggle.is_suspended = not user_to_toggle.is_suspended
    status = "suspended" if user_to_toggle.is_suspended else "reinstated"
    
    log_entry = ActivityLog(user_id=current_user.id, action='ADMIN_USER_STATUS_CHANGE', details=f"Admin {status} user '{user_to_toggle.full_name}'.")
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'message': f'User {status} successfully.'}), 200


@admin_bp.route('/lesson-logs', methods=['GET'])
@admin_required
def get_lesson_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    query = db.session.query(
        LessonLog,
        User.full_name.label('teacher_name'),
        TutorRequest.subjects.label('request_subject')
    ).join(User, User.id == LessonLog.teacher_id).join(TutorRequest, TutorRequest.id == LessonLog.request_id)
    
    pagination = query.order_by(LessonLog.lesson_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    
    result = {
        'logs': [{
            'id': log.LessonLog.id, 'date': log.LessonLog.lesson_date.strftime('%Y-%m-%d'),
            'teacherName': log.teacher_name, 'subject': log.request_subject,
            'duration': log.LessonLog.duration_hours, 'notes': log.LessonLog.teacher_notes,
            'status': log.LessonLog.status
        } for log in logs],
        'total': pagination.total, 'pages': pagination.pages, 'current_page': pagination.page
    }
    return jsonify(result), 200

# --- ADMIN MANAGEMENT ENDPOINTS ---

@admin_bp.route('/create-new-admin', methods=['POST'])
@admin_required
def create_new_admin():
    data = request.get_json()
    email = data.get('email')
    full_name = data.get('fullName')
    password = data.get('password')

    if not all([email, full_name, password]):
        return jsonify(message="Missing required fields"), 400

    if User.query.filter_by(email=email).first():
        return jsonify(message="Email already exists"), 400

    new_admin = User(
        email=email,
        full_name=full_name,
        role='admin',
        id_verification_status='Verified' # Admins effectively verified by creator
    )
    new_admin.set_password(password)
    db.session.add(new_admin)
    
    log_entry = ActivityLog(
        user_id=current_user.id, 
        action='ADMIN_CREATED_ADMIN', 
        details=f"Admin created new admin account for '{full_name}' ({email})."
    )
    db.session.add(log_entry)
    db.session.commit()

    return jsonify(message="New admin created successfully"), 201

@admin_bp.route('/list-admins', methods=['GET'])
@admin_required
def list_admins():
    # List all admins except potentially special super-admins if we had that distinction,
    # but for now list all with role='admin'.
    admins = User.query.filter_by(role='admin').all()
    result = [{
        'id': a.id,
        'name': a.full_name,
        'email': a.email,
        'isCurrent': a.id == current_user.id
    } for a in admins]
    return jsonify(result), 200

@admin_bp.route('/delete-admin/<int:admin_id>', methods=['DELETE'])
@admin_required
def delete_admin(admin_id):
    if admin_id == current_user.id:
        return jsonify(message="You cannot delete yourself."), 403
        
    admin_to_delete = User.query.get_or_404(admin_id)
    if admin_to_delete.role != 'admin':
        return jsonify(message="User is not an admin"), 400

    # Optional: Prevent deleting the "original" super admin if known by ID (e.g., ID 1)
    # if admin_to_delete.id == 1:
    #     return jsonify(message="Cannot delete the root super admin"), 403

    db.session.delete(admin_to_delete)
    
    log_entry = ActivityLog(
        user_id=current_user.id, 
        action='ADMIN_DELETED_ADMIN', 
        details=f"Admin deleted admin account '{admin_to_delete.full_name}' ({admin_to_delete.email})."
    )
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify(message="Admin deleted successfully"), 200