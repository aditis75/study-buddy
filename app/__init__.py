from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    login_manager.init_app(app)

    from .auth import bp as auth_bp
    from .profile import bp as profile_bp
    from .study_sessions import bp as sessions_bp
    from .notifications import bp as notif_bp
    from .sos import bp as sos_bp

    from .dashboard import bp as dashboard_bp
    from .buddies import bp as buddies_bp
    from .forum import bp as forum_bp
    from .resources import bp as resources_bp
    from .admin import bp as admin_bp

    for blueprint in (
        auth_bp, profile_bp, sessions_bp, notif_bp, sos_bp,
        dashboard_bp, buddies_bp, forum_bp, resources_bp, admin_bp
    ):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    return app
