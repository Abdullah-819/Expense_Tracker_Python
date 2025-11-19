from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime, date
import json
import os
import uuid
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
mail = Mail(app)  # Initialize Flask-Mail

# ------------------- Models -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # email verification
    verification_token = db.Column(db.String(200), nullable=True)  # token for email

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(200))
    date = db.Column(db.Date, default=date.today)

# ------------------- Routes -------------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- SIGNUP WITH EMAIL VERIFICATION ----------
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

        # Generate verification token
        token = str(uuid.uuid4())
        user = User(username=username, email=email, password=password, verification_token=token)
        db.session.add(user)
        db.session.commit()

        # Send verification email
        verification_link = url_for('verify_email', token=token, _external=True)
        msg = Message(
            "Confirm your Expense Tracker account",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Hi {username},\n\nPlease confirm your account by clicking this link:\n{verification_link}"
        mail.send(msg)

        flash("Signup successful! Please check your email to verify your account.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

# ---------- EMAIL VERIFICATION ROUTE ----------
@app.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first_or_404()
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    flash("Email verified! You can now log in.", "success")
    return redirect(url_for('login'))

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash("Please verify your email before logging in.", "warning")
                return redirect(url_for('login'))
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
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
        categories[e.category] = categories.get(e.category,0)+e.amount
    if not categories:
        categories = {'No Data':0}
    return render_template('dashboard.html', expenses=expenses, total=total, categories=json.dumps(categories))

# ---------- ADD EXPENSE ----------
@app.route('/add-expense', methods=['GET','POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash('Please enter a valid amount.', 'danger')
            return redirect(url_for('add_expense'))
        category = request.form.get('category','Other')
        note = request.form.get('note','')
        date_str = request.form.get('date','')
        if date_str:
            try:
                expense_date = datetime.strptime(date_str,'%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('add_expense'))
        else:
            expense_date = date.today()
        new_exp = Expense(user_id=session['user_id'], amount=amount, category=category, note=note, date=expense_date)
        db.session.add(new_exp)
        db.session.commit()
        flash('Expense added.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html')

# ---------- VIEW EXPENSES ----------
@app.route('/expenses')
def expenses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=expenses)

# ---------- EDIT EXPENSE ----------
@app.route('/edit-expense/<int:expense_id>', methods=['GET','POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != session['user_id']:
        flash('Not authorized to edit.', 'danger')
        return redirect(url_for('expenses'))
    if request.method=='POST':
        try:
            expense.amount = float(request.form['amount'])
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('edit_expense', expense_id=expense.id))
        expense.category = request.form['category']
        expense.note = request.form.get('note','')
        date_str = request.form.get('date')
        if date_str:
            expense.date = datetime.strptime(date_str,'%Y-%m-%d').date()
        db.session.commit()
        flash('Expense updated.', 'success')
        return redirect(url_for('expenses'))
    return render_template('edit_expense.html', expense=expense)

# ---------- DELETE EXPENSE ----------
@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != session['user_id']:
        flash('Not authorized to delete.', 'danger')
        return redirect(url_for('expenses'))
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully.', 'success')
    return redirect(url_for('expenses'))

# ---------- RUN APP ----------
if __name__=='__main__':
    if not os.path.exists('database'):
        os.makedirs('database')
    with app.app_context():
        db.create_all()
    app.run(debug=True)
