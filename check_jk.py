import imaplib
import email
from email.header import decode_header
import os

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
IMAP_SERVER = "imap.gmail.com"

try:
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(SENDER_EMAIL, APP_PASSWORD)
    mail.select("inbox")
    status, response = mail.search(None, '(FROM "jkbarber.fics@gmail.com")')
    mail_ids = response[0].split()
    print(f"Found {len(mail_ids)} messages from JK Barber")
    for num in mail_ids:
        status, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        print(f"Subject: {subject}\nBody: {body}\n---\n")
    mail.logout()
except Exception as e:
    print(f"Error: {e}")
