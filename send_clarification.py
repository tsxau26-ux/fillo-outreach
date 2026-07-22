#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
RECIPIENT = "jkbarber.fics@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SUBJECT = "Re: question about empty slots at JK Barber FICS31"

BODY = """Hi JK Barber Team,

Thank you for your reply!

Just to clarify — Fillo is NOT a replacement for your existing appointment or booking management software.

Fillo works alongside your current setup specifically for unexpected cancellations and quiet hours. Whenever a client cancels last minute or you have an empty slot, you can send an automated 1-click alert to your regular clients via Telegram with a direct booking link to claim the slot.

It requires 0 software changes on your end and takes under 5 minutes to set up.

Since we offer a 1-month free trial with zero commitment, would you be open to trying it out for 2 weeks to see how many lost slots it recovers for JK Barber?

Best regards,
Fillo Team
"""

def send_email():
    if not SENDER_EMAIL or not APP_PASSWORD:
        print("Missing credentials!")
        return False
        
    msg = MIMEMultipart()
    msg["From"] = f"Fillo Team <{SENDER_EMAIL}>"
    msg["To"] = RECIPIENT
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(BODY, "plain"))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Clarification email sent successfully to {RECIPIENT}!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

if __name__ == "__main__":
    send_email()
