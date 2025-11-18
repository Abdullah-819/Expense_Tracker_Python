import os

# Get the absolute path of the project folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "supersecretkey123"  # for session security
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database/db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
