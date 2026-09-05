import smtplib
import os

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    print("SMTP login successful")
    server.quit()
except Exception as e:
    print(f"SMTP error: {e}")
