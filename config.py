import os

class Config:
    # ---------------- Flask settings ----------------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

    # ---------------- Database ----------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_DIR = os.path.join(BASE_DIR, 'database')
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DB_DIR, 'expense_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------------- Brevo / Sendinblue API ----------------
    BREVO_API_KEY = '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'
    SENDER_EMAIL = 'ranaabdullah228.ar@gmail.com'

    # ---------------- Public URL for email verification ----------------
    # Replace this with your current ngrok URL whenever it changes
    BASE_URL = 'https://hypochondriacally-prepigmental-lore.ngrok-free.dev'
