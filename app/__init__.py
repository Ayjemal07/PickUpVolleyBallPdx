from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager

# db = SQLAlchemy()
# login_manager = LoginManager()
# login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object('config.Config')

    # # Initialize extensions
    # db.init_app(app)
    # login_manager.init_app(app)
    # migrate.init_app(app, db)

    # # Register Blueprints
    from .views import main
    from .authentication.auth_routes import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    
    # with app.app_context():
    #     # Create database tables based on models
    #     db.create_all()

    return app
