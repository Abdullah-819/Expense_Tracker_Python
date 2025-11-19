import os
import uuid
import json
import requests
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# ------------------- App Initialization -------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

db = SQLAlchemy(app)

# ------------------- Models -------------------
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

# ------------------- Helper Function (Brevo REST API) -------------------
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
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201, 202]:
            print(f"Email sent to {recipient}")
        else:
            print(f"Failed to send email: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception while sending email: {e}")

# ------------------- Routes -------------------
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

        existing_user = User.query.filter((User.username==username)|(User.email==email)).first()
        if existing_user:
            flash('Username or Email already exists!', 'danger')
            return redirect(url_for('signup'))

        token = str(uuid.uuid4())
        user = User(username=username, email=email, password=password, verification_token=token)
        db.session.add(user)
        db.session.commit()  # commit before sending email

        verification_link = url_for('verify_email', token=token, _external=True)
        body = f"Hi {username},\n\nPlease confirm your account by clicking the link below:\n{verification_link}"
        send_email("Confirm your Expense Tracker account", email, body)

        flash("Signup successful! Check your email to verify your account.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# ---------- VERIFY EMAIL ----------
@app.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash("Invalid or expired token. Please try resending verification.", "danger")
        return redirect(url_for('resend_verification'))

    if user.is_verified:
        flash("Account already verified. Please log in.", "info")
        return redirect(url_for('login'))

    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    flash("Email verified! You can now log in.", "success")
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
            flash("Account already verified. Please log in.", "info")
            return redirect(url_for('login'))

        token = str(uuid.uuid4())
        user.verification_token = token
        db.session.commit()

        verification_link = url_for('verify_email', token=token, _external=True)
        body = f"Hi {user.username},\n\nPlease confirm your account by clicking the link below:\n{verification_link}"
        send_email("Resend: Confirm your Expense Tracker account", email, body)
        flash("Verification email resent! Check your inbox.", "success")
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
            flash("Invalid credentials!", "danger")
            return redirect(url_for('login'))

        if not user.is_verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for('resend_verification'))

        session['user_id'] = user.id
        session['username'] = user.username
        flash("Logged in successfully.", "success")

        body = f"Hi {user.username},\n\nYou logged in on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        send_email("New Login Alert", user.email, body)
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount
    if not categories:
        categories = {'No Data': 0}

    return render_template('dashboard.html', expenses=expenses, total=total, categories=json.dumps(categories))

# ---------- ADD EXPENSE ----------
@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for('add_expense'))

        category = request.form.get('category', 'Other')
        note = request.form.get('note', '')
        date_str = request.form.get('date', '')
        expense_date = date.today()
        if date_str:
            try:
                expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format.", "danger")
                return redirect(url_for('add_expense'))

        new_exp = Expense(user_id=session['user_id'], amount=amount, category=category, note=note, date=expense_date)
        db.session.add(new_exp)
        db.session.commit()
        flash("Expense added.", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html')

# ---------- RUN APP ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
