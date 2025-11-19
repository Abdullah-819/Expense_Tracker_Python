import os

class Config:
    SECRET_KEY = "supersecretkey123"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "database/db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Brevo REST API
    BREVO_API_KEY = "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"
    SENDER_EMAIL = "ranaabdullah228.ar@gmail.com"
