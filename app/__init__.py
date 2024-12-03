from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from app.models import db, login_manager

# Load environment variables
load_dotenv()

# Initialize the database
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object('config.Config')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())


    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # # Register Blueprints
    from .views import main
    from .authentication.auth_routes import auth
    from .admin_routes import admin_bp
    from .api_routes import api_bp

    app.register_blueprint(auth)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main)  # Register last to avoid route conflicts


    return app
