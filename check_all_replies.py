import imaplib, email, os
from email.header import decode_header

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(SENDER_EMAIL, APP_PASSWORD)
mail.select("inbox")

# Search all emails NOT from joinfillo and NOT from google
_, response = mail.search(None, 'ALL')
mail_ids = response[0].split()

replies = []
for num in mail_ids[-50:]:  # Check last 50 emails
    _, data = mail.fetch(num, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
    raw_header = data[0][1].decode("utf-8", errors="ignore")
    
    if "joinfillo@gmail.com" not in raw_header and "google.com" not in raw_header:
        replies.append(raw_header.strip())

print(f"Found {len(replies)} incoming messages:")
for r in replies:
    print("---")
    print(r)

mail.logout()
