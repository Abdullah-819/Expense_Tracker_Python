from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime

# ✅ Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# ✅ Create database object
db = SQLAlchemy(app)

# ---------------------- MODELS ---------------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(200))
    date = db.Column(db.String(20), default=datetime.now().strftime("%Y-%m-%d"))

# ---------------------- ROUTES ---------------------- #

@app.route("/")
def index():
    return render_template("index.html")

# (other routes follow here...)

# ---------------------- RUN ---------------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
