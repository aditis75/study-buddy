import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "dev-secret-change-later"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "studybuddy.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
