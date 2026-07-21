#!/usr/bin/env python3
import os
import time
import json
import csv
import ssl
import urllib.request
import urllib.parse
import imaplib
import email
from email.header import decode_header

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8827856631:AAGTJvC7UkOqVHtTEgbV4WxK_Ir8kE0IDAQ")
ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5219669099")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = "tsxau26-ux/fillo-outreach"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
IMAP_SERVER = "imap.gmail.com"

CSV_FILE = "fillo_leads.csv"
STATE_FILE = "outreach_state.json"

def send_telegram_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=context) as resp:
            pass
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_status_summary():
    total_leads = 0
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            total_leads = max(0, len(f.readlines()) - 1)
            
    sent_emails = []
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            sent_emails = data.get("sent_emails", [])
            
    pending = max(0, total_leads - len(sent_emails))
    
    return f"""📊 **Fillo Outreach Status**

• **Total Database Leads:** {total_leads}
• **Successfully Sent:** {len(sent_emails)}
• **Pending Leads:** {pending}
• **Daily Limit:** 50 emails/day

Use `/run` to start sending or `/replies` to check inbox!"""

def check_unread_replies():
    if not SENDER_EMAIL or not APP_PASSWORD:
        return "⚠️ Missing email credentials."
        
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(SENDER_EMAIL, APP_PASSWORD)
        mail.select("inbox")
        
        status, response = mail.search(None, 'UNSEEN')
        if status != "OK" or not response[0]:
            mail.logout()
            return "📬 No unread replies in your inbox."
            
        mail_ids = response[0].split()
        res = [f"📬 **Found {len(mail_ids)} unread message(s):**\n"]
        
        for num in mail_ids[:5]: # Top 5
            status, data = mail.fetch(num, '(RFC822)')
            if status != "OK":
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
                
            from_, encoding = decode_header(msg["From"])[0]
            if isinstance(from_, bytes):
                from_ = from_.decode(encoding or "utf-8", errors="ignore")
                
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")
                
            snippet = body.strip().replace("\n", " ")[:100]
            res.append(f"• **From:** {from_}\n  **Subject:** {subject}\n  **Snippet:** {snippet}...\n")
            
        mail.logout()
        return "\n".join(res)
    except Exception as e:
        return f"Error checking replies: {e}"

def trigger_github_workflow():
    if not GITHUB_TOKEN:
        return "⚠️ Missing GitHub Access Token."
        
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/outreach.yml/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "FilloBot",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"ref": "main"}).encode("utf-8")
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=context) as resp:
            if resp.status == 204:
                return "🚀 **Outreach campaign run triggered successfully on GitHub Actions!**"
            else:
                return f"Response code: {resp.status}"
    except Exception as e:
        return f"Error triggering workflow: {e}"

def main():
    print("=======================================")
    print("      Fillo Telegram Command Bot       ")
    print("=======================================")
    print(f"Listening for commands from Chat ID: {ALLOWED_CHAT_ID}...\n")

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=context) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for result in data.get("result", []):
                offset = result["update_id"] + 1
                message = result.get("message", {})
                chat = message.get("chat", {})
                chat_id = str(chat.get("id"))
                text = message.get("text", "").strip()

                if chat_id != ALLOWED_CHAT_ID:
                    continue

                print(f"Received command: '{text}' from {chat_id}")

                if text in ["/start", "/help"]:
                    reply = """🤖 **Fillo Outreach Bot Commands**

• `/status` - Check campaign progress and lead stats.
• `/replies` - Check unread inbox replies.
• `/run` - Instantly start sending outreach emails.
• `/help` - Show this menu."""
                    send_telegram_msg(chat_id, reply)

                elif text == "/status":
                    send_telegram_msg(chat_id, get_status_summary())

                elif text == "/replies":
                    send_telegram_msg(chat_id, check_unread_replies())

                elif text == "/run":
                    send_telegram_msg(chat_id, "⏳ Triggering cloud campaign...")
                    res = trigger_github_workflow()
                    send_telegram_msg(chat_id, res)

        except Exception as e:
            print(f"Error in polling loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
