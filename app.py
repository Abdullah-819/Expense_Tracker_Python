# app.py
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime, date
import json
import os

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

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
    date = db.Column(db.Date, default=date.today)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = generate_password_hash(request.form["password"])

        existing_user = User.query.filter((User.username==username)|(User.email==email)).first()
        if existing_user:
            flash("Username or Email already exists!", "danger")
            return redirect(url_for("signup"))

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Signup successful. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != session["user_id"]:
        flash("You are not authorized to delete this expense.", "danger")
        return redirect(url_for("expenses"))
    
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted successfully.", "success")
    return redirect(url_for("expenses"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Credentials!", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not categories:
        categories = {"No Data": 0}

    return render_template("dashboard.html", expenses=expenses, total=total, categories=json.dumps(categories))

@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
        except ValueError:
            flash("Please enter a valid amount.", "danger")
            return redirect(url_for("add_expense"))

        category = request.form.get("category", "Other")
        note = request.form.get("note", "")
        date_str = request.form.get("date", "")

        if date_str:
            try:
                expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format.", "danger")
                return redirect(url_for("add_expense"))
        else:
            expense_date = date.today()

        new_exp = Expense(user_id=session["user_id"], amount=amount, category=category, note=note, date=expense_date)
        db.session.add(new_exp)
        db.session.commit()
        flash("Expense added.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")

@app.route("/expenses")
def expenses():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    return render_template("expenses.html", expenses=expenses)

if __name__ == "__main__":
    if not os.path.exists("database"):
        os.makedirs("database")
    with app.app_context():
        db.create_all()
    app.run(debug=True)


# DELETE EXPENSE
@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session["user_id"]:
        flash("You are not authorized to delete this expense.", "danger")
        return redirect(url_for("expenses"))

    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted successfully.", "success")
    return redirect(url_for("expenses"))

# EDIT EXPENSE
@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != session["user_id"]:
        flash("You are not authorized to edit this expense.", "danger")
        return redirect(url_for("expenses"))

    if request.method == "POST":
        try:
            expense.amount = float(request.form["amount"])
        except ValueError:
            flash("Invalid amount entered.", "danger")
            return redirect(url_for("edit_expense", expense_id=expense.id))
        
        expense.category = request.form["category"]
        expense.note = request.form.get("note", "")
        date_str = request.form.get("date")
        if date_str:
            expense.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        db.session.commit()
        flash("Expense updated successfully.", "success")
        return redirect(url_for("expenses"))

    return render_template("edit_expense.html", expense=expense)
