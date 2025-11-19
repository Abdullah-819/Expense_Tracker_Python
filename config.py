import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database/db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Brevo SMTP settings
    MAIL_SERVER = 'smtp-relay.brevo.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('BREVO_SMTP_LOGIN')
    MAIL_PASSWORD = os.getenv('BREVO_SMTP_PASSWORD')
