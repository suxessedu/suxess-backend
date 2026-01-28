from flask import Blueprint, request, jsonify, session
from app.models.user_model import User
from app.models.teacher_profile_model import TeacherProfile
from app.extensions import db, mail
from flask_login import login_user, logout_user, current_user
import os
import random
from flask_mail import Message

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/setup-super-admin', methods=['POST'])
def setup_super_admin():
    super_admin_email = os.environ.get('SUPER_ADMIN_EMAIL')
    if User.query.filter_by(role='admin').first():
        return jsonify({'message': 'An admin account already exists.'}), 409
    
    data = request.get_json()
    password = data.get('password')
    full_name = data.get('fullName')
    
    if not password or not full_name:
        return jsonify({'message': 'Full name and password are required'}), 400

    otp = str(random.randint(100000, 999999))
    session['admin_setup_otp'] = otp
    session['admin_setup_data'] = {'email': super_admin_email, 'password': password, 'fullName': full_name}
    
    msg = Message('Your Suxess Admin OTP', recipients=[super_admin_email])
    msg.body = f'Your One-Time Password to create the Super Admin account is: {otp}'
    mail.send(msg)

    return jsonify({'message': 'OTP sent to super admin email'}), 200

@auth_bp.route('/verify-super-admin-otp', methods=['POST'])
def verify_super_admin_otp():
    data = request.get_json()
    otp = data.get('otp')

    if 'admin_setup_otp' not in session or session.get('admin_setup_otp') != otp:
        return jsonify({'message': 'Invalid or expired OTP'}), 401
    
    admin_data = session.pop('admin_setup_data', None)
    session.pop('admin_setup_otp', None)
    
    if not admin_data:
        return jsonify({'message': 'Session expired, please start over.'}), 400

    # THE DEFINITIVE FIX STARTS HERE
    existing_user = User.query.filter_by(email=admin_data['email']).first()
    
    if existing_user:
        # If user exists, update their role to admin and set the new password
        admin_user = existing_user
        admin_user.role = 'admin'
        admin_user.full_name = admin_data['fullName']
        admin_user.set_password(admin_data['password'])
    else:
        # If user does not exist, create a new one
        admin_user = User(
            email=admin_data['email'],
            full_name=admin_data['fullName'],
            role='admin'
        )
        admin_user.set_password(admin_data['password'])
        db.session.add(admin_user)

    db.session.commit()
    
    login_user(admin_user)
    
    return jsonify({ 'user': { 'id': admin_user.id, 'fullName': admin_user.full_name, 'email': admin_user.email, 'role': admin_user.role }}), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(key in data for key in ['email', 'password', 'fullName', 'role']):
        return jsonify({'message': 'Missing required fields'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User with this email already exists'}), 409
    new_user = User(email=data['email'], full_name=data['fullName'], role=data['role'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    if new_user.role == 'teacher':
        new_profile = TeacherProfile(user=new_user, is_complete=False)
        db.session.add(new_profile)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if not user or not user.check_password(data.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    login_user(user)
    
    profile_complete = True
    if user.role == 'teacher':
        profile = user.profile
        profile_complete = profile.is_complete if profile else False

    return jsonify({
        'user': {
            'id': user.id,
            'fullName': user.full_name,
            'email': user.email,
            'role': user.role,
            'profileComplete': profile_complete,
            'verificationStatus': user.id_verification_status,
            'isPremium': user.is_premium, # Add premium status to response
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200