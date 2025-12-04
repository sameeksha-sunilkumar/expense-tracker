import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

EMAIL = os.getenv("ALERT_EMAIL")
PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")

def send_budget_alert(to_email: str, category: str, spent, budget):
    if not EMAIL or not PASSWORD:
        print("Email credentials not set; skipping sending email.")
        return

    subject = f"Budget Alert: {category}"
    body = (
        f"Expense Tracker Alert\n\n"
        f"Category: {category}\n"
        f"Spent: {spent}\n"
        f"Budget: {budget}\n\n"
        f"Please check your expenses."
    )

    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Alert email sent to {to_email}")
    except Exception as e:
        print("Error sending email:", e)
