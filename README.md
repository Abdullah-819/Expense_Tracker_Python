# 💰 Expense Tracker Web App  
A full-featured **Expense Tracking** application built with **Flask**, **SQLite**, **Bootstrap**, and **Brevo (Sendinblue)** for email verification.  
This app allows users to manage expenses, view analytics, receive login alerts, and verify their accounts via email using secure token-based verification.

---

## 🚀 Features

### 🔐 Authentication & Security
- Secure **user signup**
- **Email verification** with unique UUID token
- Resend verification link
- **Login alerts** sent to the user’s email
- Secure password hashing (Werkzeug)

### 📊 Expense Management
- Add expenses  
- Edit expenses  
- Delete expenses  
- View detailed list of expenses  
- Category-wise analytics  
- Dashboard summary with total expenses

### 🌐 External Integrations
- **Brevo SMTP API** for sending email verification + login notifications
- **ngrok support** for exposing local server publicly

---

## 📸 Screenshots
TBC

---

## 🛠 Tech Stack

| Category | Technologies |
|----------|--------------|
| Backend | Flask (Python), SQLite, SQLAlchemy |
| Frontend | Bootstrap 5, HTML, CSS |
| Email | Brevo (Sendinblue) SMTP API |
| Hosting (Local) | ngrok |
| Security | UUID tokens, password hashing |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker

