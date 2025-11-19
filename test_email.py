import requests
from config import Config

url = "https://api.brevo.com/v3/smtp/email"

payload = {
    "sender": {"name": Config.SENDER_NAME, "email": Config.SENDER_EMAIL},
    "to": [{"email": "ranaabdullah228.ar@gmail.com"}],
    "subject": "Test Email from Expense Tracker",
    "textContent": "Hello! This is a test email sent via Brevo REST API."
}

headers = {
    "Content-Type": "application/json",
    "api-key": Config.BREVO_API_KEY
}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code, response.text)
