import smtplib
from email.message import EmailMessage
import os

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
RECIPIENT = "jkbarber.fics@gmail.com"

msg = EmailMessage()
msg['Subject'] = "Re: Free for 1 month: fill empty chairs at JK Barber FICS31"
msg['From'] = SENDER_EMAIL
msg['To'] = RECIPIENT

body = """Hi Jittakorn,

Apologies for the delayed response!

To make things as easy as possible for you, could you please share your WhatsApp or LINE contact number/ID? 

Our team will reach out directly to walk you through the setup step-by-step and answer any questions you might have. It's very quick and easy.

Looking forward to getting you set up!

Best regards,

Fillo Team"""

msg.set_content(body)

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()
    print("Reply successfully sent to JK Barber!")
except Exception as e:
    print(f"Error sending email: {e}")
