
# from flask import Flask
# from flask import render_template

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('home.html')

# if __name__ == '__main__':
#     app.run(debug=True)

# from flask import Flask

# def create_app():
#     app = Flask(__name__)

#     # # Register Blueprints
#     # from .app.views import main
#     # app.register_blueprint(main)

    
#     # with app.app_context():
#     #     # Create database tables based on models
#     #     db.create_all()

#     return "Hello"



from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # app.run(debug=True)
    host = 'localhost'  # Listen on all network interfaces
    port = int(5000)
    if os.name == "nt":
        app.run(debug=True)
    else:
        app.run(host=host, port=port)
