import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "supersecretkey123"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database/db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False