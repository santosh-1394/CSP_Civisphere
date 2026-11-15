
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user

from config import Config
from extensions import login_manager, csrf

# Import Blueprints
from app.routes.auth import auth
from app.routes.services import services_bp
from app.routes.complaints import complaints_bp
from app.routes.donors import donors_bp
from app.routes.contacts import contacts_bp
from app.routes.notifications import notifications_bp
from app.routes.feedback import feedback_bp
from app.routes.chatbot import chatbot_bp
from app.routes.locations import locations_bp
from app.routes.admin import admin_bp
from app.routes.emergency_services import emergency_services_bp


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth)
    app.register_blueprint(services_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(donors_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(emergency_services_bp)

    # Load logged-in user
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.get_by_id(user_id)

    # Public Homepage
    @app.route("/")
    def home():
        return render_template("landing.html")

    # Citizen Dashboard
    @app.route("/dashboard")
    def citizen_dashboard():

        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if (current_user.role or "").strip().lower() == "admin":
            return redirect(url_for("admin.admin_dashboard"))

        return render_template("index.html")

    return app


app = create_app()

