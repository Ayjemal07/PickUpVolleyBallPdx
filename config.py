#This file hols configuration settings

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for flask session management
    SECRET_KEY = os.getenv('FLASK_SESSION')

    # Other API keys

    

