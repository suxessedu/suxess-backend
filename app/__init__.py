from flask import Flask
from config import Config
from .extensions import db, migrate, bcrypt, login_manager, mail
from flask_cors import CORS

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    with app.app_context():
        # THE DEFINITIVE FIX: Import the new model here so the database tool can see it.
        from .models import user_model, teacher_profile_model, request_model, activity_log_model, lesson_log_model, notification_model
        
        from .routes.auth import auth_bp
        from .routes.teachers import teachers_bp
        from .routes.parents import parents_bp
        from .routes.users import users_bp
        from .routes.admin import admin_bp
        from .routes.requests import requests_bp
        from .routes.messages import messages_bp
        from .routes.common import common_bp
        from .routes.notifications import notifications_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(teachers_bp, url_prefix='/api/teachers')
        app.register_blueprint(parents_bp, url_prefix='/api/parents')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(requests_bp, url_prefix='/api/requests')
        app.register_blueprint(messages_bp, url_prefix='/api/messages')
        app.register_blueprint(common_bp, url_prefix='/api/common')
        app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    return app