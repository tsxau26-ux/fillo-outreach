#!/usr/bin/env python3
import os
import imaplib
import email
import urllib.request
import urllib.parse
import ssl
from email.header import decode_header

# Configuration
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8827856631:AAGTJvC7UkOqVHtTEgbV4WxK_Ir8kE0IDAQ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5219669099")
IMAP_SERVER = "imap.gmail.com"

BOUNCE_SENDERS = ["mailer-daemon", "postmaster", "no-reply", "noreply", "accounts.google.com"]
BOUNCE_SUBJECTS = ["delivery status notification", "undelivered mail", "failure notice", "mail delivery failed", "out of office", "security alert", "2-step verification", "finish setting up"]

def is_real_human_reply(from_str, subject_str):
    from_lower = str(from_str).lower()
    subj_lower = str(subject_str).lower()
    if any(b in from_lower for b in BOUNCE_SENDERS):
        return False
    if any(s in subj_lower for s in BOUNCE_SUBJECTS):
        return False
    return True

def send_telegram_alert(token, chat_id, message):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=context) as response:
            pass
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def main():
    print("=======================================")
    print("        Fillo Outreach Reply Checker   ")
    print("=======================================\n")
    
    if not SENDER_EMAIL or not APP_PASSWORD:
        print("Missing credentials in environment variables.")
        return

    try:
        print("Connecting to Gmail IMAP server...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(SENDER_EMAIL, APP_PASSWORD)
        print("Authenticated successfully.")
        
        mail.select("inbox")
        
        # Search for unread emails in inbox
        status, response = mail.search(None, 'UNSEEN')
        
        if status != "OK":
            print("Failed to search inbox.")
            return
            
        mail_ids = response[0].split()
        print(f"Found {len(mail_ids)} unread email(s) in inbox:\n")
        
        for num in mail_ids:
            status, data = mail.fetch(num, '(RFC822)')
            if status != "OK":
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Decode Subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
                
            # Decode From
            from_, encoding = decode_header(msg["From"])[0]
            if isinstance(from_, bytes):
                from_ = from_.decode(encoding or "utf-8", errors="ignore")

            if not is_real_human_reply(from_, subject):
                print(f"Skipping automated/bounce message from: {from_} ({subject})")
                continue
                
            # Get body snippet
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                except Exception:
                    pass
            
            snippet = body.strip().replace("\n", " ").replace("\r", "")[:150]
            
            print(f"From: {from_}")
            print(f"Subject: {subject}")
            print(f"Snippet: {snippet}...")
            print("-" * 50)
            
            # Send alert to Telegram
            alert_msg = f"📩 **NEW OUTREACH REPLY**\n\n**From:** {from_}\n**Subject:** {subject}\n**Snippet:** {snippet}..."
            send_telegram_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, alert_msg)
            
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error checking replies: {e}")

if __name__ == "__main__":
    main()

