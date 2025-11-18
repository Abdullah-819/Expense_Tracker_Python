from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime
import json
import os

# ------------------- CREATE APP ------------------- #
app = Flask(__name__)
app.config.from_object(Config)

# ------------------- DATABASE ------------------- #
db = SQLAlchemy(app)

# ------------------- MODELS ------------------- #
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

# ------------------- ROUTES ------------------- #
@app.route("/")
def index():
    return render_template("index.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        # Check if username or email exists
        existing_user = User.query.filter((User.username==username)|(User.email==email)).first()
        if existing_user:
            return "Username or Email already exists!"

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Credentials!"
    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    expenses = Expense.query.filter_by(user_id=user_id).all()
    total = sum(e.amount for e in expenses)

    # Categories for chart
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not categories:
        categories = {"No Data": 0}

    return render_template("dashboard.html",
                           expenses=expenses,
                           total=total,
                           categories=json.dumps(categories))

# ---------- ADD EXPENSE ----------
@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        note = request.form["note"]

        new_exp = Expense(
            user_id=session["user_id"],
            amount=amount,
            category=category,
            note=note
        )
        db.session.add(new_exp)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_expense.html")

# ---------- VIEW ALL EXPENSES ----------
@app.route("/expenses")
def expenses():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    expenses = Expense.query.filter_by(user_id=user_id).all()
    return render_template("expenses.html", expenses=expenses)

# ------------------- RUN APP ------------------- #
if __name__ == "__main__":
    # Create database folder if it doesn't exist
    if not os.path.exists("database"):
        os.makedirs("database")
    # Create tables
    with app.app_context():
        db.create_all()
    app.run(debug=True)
