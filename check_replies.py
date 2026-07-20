#!/usr/bin/env python3
import os
import imaplib
import email
from email.header import decode_header

# Configuration
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
IMAP_SERVER = "imap.gmail.com"

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
                
            print(f"From: {from_}")
            print(f"Subject: {subject}")
            
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
            
            snippet = body.strip().replace("\n", " ").replace("\r", "")[:120]
            print(f"Snippet: {snippet}...")
            print("-" * 50)
            
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error checking replies: {e}")

if __name__ == "__main__":
    main()
