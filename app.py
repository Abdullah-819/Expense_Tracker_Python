import os
import uuid
import json
import requests
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# ------------------- APP INITIALIZATION -------------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

db = SQLAlchemy(app)

# ------------------- DATABASE MODELS -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(200), nullable=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(200))
    date = db.Column(db.Date, default=date.today)

# ------------------- SEND EMAIL (BREVO REST API) -------------------
def send_email(subject, recipient, body):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": Config.BREVO_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "ExpenseTrackerApp", "email": Config.SENDER_EMAIL},
        "to": [{"email": recipient}],
        "subject": subject,
        "textContent": body
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print("Brevo Response:", response.status_code, response.text)
    except Exception as e:
        print("Email sending failed:", e)

# ------------------- ROUTES -------------------

@app.route('/')
def index():
    return render_template('index.html')


# ---------- SIGNUP ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = generate_password_hash(request.form['password'])

        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash("Username or Email already exists!", "danger")
            return redirect(url_for('signup'))

        token = str(uuid.uuid4())
        new_user = User(username=username, email=email, password=password, verification_token=token)
        db.session.add(new_user)
        db.session.commit()

        verification_link = f"{Config.BASE_URL}/verify-email/{token}"
        body = f"Hello {username},\n\nVerify your account:\n{verification_link}"

        send_email("Verify Your Expense Tracker Account", email, body)
        flash("Signup successful! Check your email for verification.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


# ---------- VERIFY EMAIL ----------
@app.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        flash("Invalid or expired link.", "danger")
        return redirect(url_for('login'))

    user.is_verified = True
    user.verification_token = None
    db.session.commit()

    flash("Your email is verified! Please log in.", "success")
    return redirect(url_for('login'))


# ---------- RESEND VERIFICATION ----------
@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form['email'].strip()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email.", "danger")
            return redirect(url_for('resend_verification'))

        if user.is_verified:
            flash("Account is already verified.", "info")
            return redirect(url_for('login'))

        token = str(uuid.uuid4())
        user.verification_token = token
        db.session.commit()

        verification_link = f"{Config.BASE_URL}/verify-email/{token}"
        body = f"Hello {user.username},\n\nVerify your account:\n{verification_link}"

        send_email("Resend Verification", email, body)
        flash("Verification link sent!", "success")
        return redirect(url_for('login'))

    return render_template('resend_verification.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid username or password.", "danger")
            return redirect(url_for('login'))

        if not user.is_verified:
            flash("Verify your email first.", "warning")
            return redirect(url_for('resend_verification'))

        session['user_id'] = user.id
        session['username'] = user.username

        login_msg = f"Login detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_email("Login Notification", user.email, login_msg)

        return redirect(url_for('dashboard'))

    return render_template('login.html')


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    expenses = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not categories:
        categories = {"No Data": 0}

    return render_template(
        'dashboard.html',
        expenses=expenses,
        total=total,
        categories=json.dumps(categories)
    )


# ---------- VIEW ALL EXPENSES ----------
@app.route('/expenses')
def expenses():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    expenses = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=expenses)


# ---------- ADD EXPENSE ----------
@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        note = request.form['note']
        date_str = request.form['date']

        expense_date = date.today()
        if date_str:
            expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        new_expense = Expense(
            user_id=session['user_id'],
            amount=amount,
            category=category,
            note=note,
            date=expense_date
        )

        db.session.add(new_expense)
        db.session.commit()

        flash("Expense added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html')


# ---------- EDIT EXPENSE ----------
@app.route('/edit-expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session['user_id']:
        flash("You cannot edit this expense.", "danger")
        return redirect(url_for('expenses'))

    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.category = request.form['category']
        expense.note = request.form['note']

        date_str = request.form['date']
        if date_str:
            expense.date = datetime.strptime(date_str, "%Y-%m-%d").date()

        db.session.commit()
        flash("Expense updated!", "success")
        return redirect(url_for('expenses'))

    return render_template('edit_expense.html', expense=expense)


# ---------- DELETE EXPENSE ----------
@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != session['user_id']:
        flash("You cannot delete this expense.", "danger")
        return redirect(url_for('expenses'))

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully!", "success")
    return redirect(url_for('expenses'))


# ---------- RUN APP ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
