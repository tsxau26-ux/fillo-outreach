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
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "tsxau26-ux/fillo-outreach"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
IMAP_SERVER = "imap.gmail.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "fillo_leads.csv")
STATE_FILE = os.path.join(BASE_DIR, "outreach_state.json")

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
    try:
        from bounce_cleaner import run_lead_cleaning
        stats = run_lead_cleaning()
        return f"""📊 **Fillo Outreach Status**

• **Total Database Leads:** {stats['total_leads']}
• **Clean Active Leads:** {stats['clean_leads_count']}
• **Successfully Delivered:** {stats['sent_delivered']}
• **Bounced (Email Not Found):** {stats['bounced']}
• **Invalid MX Domain:** {stats['invalid_mx']}
• **Clean Pending Queue:** {stats['pending_valid']}
• **Daily Safety Limit:** 50 emails/day

Use `/run` to start sending, `/clean` to purge bounces, or `/replies` to check inbox!"""
    except Exception as e:
        return f"Error computing status: {e}"

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
        res = []
        
        for num in reversed(mail_ids):
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
                
            if not is_real_human_reply(from_, subject):
                continue

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
            if len(res) >= 5:
                break
            
        mail.logout()
        if not res:
            return "📬 No real customer replies found (bounces filtered out)."
        return f"📬 **Found {len(res)} real customer reply(ies):**\n\n" + "\n".join(res)
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
                raw_text = message.get("text", "").strip()

                if chat_id != ALLOWED_CHAT_ID:
                    print(f"Ignored message from unauthorized chat_id: {chat_id}")
                    continue

                cmd = raw_text.split("@")[0].strip().lower()
                print(f"Received command: '{raw_text}' (parsed: '{cmd}') from {chat_id}")

                if cmd in ["/start", "/help"]:
                    reply = """🤖 **Fillo Outreach Bot Commands**

• `/status` - Check campaign progress & lead stats.
• `/analytics` - View live email open & click tracking rates.
• `/replies` - Check unread inbox replies.
• `/clean` - Purge bounced & invalid email addresses.
• `/run` - Instantly start sending outreach emails.
• `/help` - Show this menu."""
                    send_telegram_msg(chat_id, reply)

                elif cmd == "/status":
                    send_telegram_msg(chat_id, get_status_summary())

                elif cmd in ["/analytics", "/opens"]:
                    try:
                        from email_analytics import get_analytics_report
                        send_telegram_msg(chat_id, get_analytics_report())
                    except Exception as e:
                        send_telegram_msg(chat_id, f"Analytics error: {e}")

                elif cmd == "/clean":
                    send_telegram_msg(chat_id, "🧹 Scanning inbox for bounces & verifying domain MX records...")
                    send_telegram_msg(chat_id, get_status_summary())

                elif cmd == "/replies":
                    send_telegram_msg(chat_id, check_unread_replies())

                elif cmd == "/run":
                    send_telegram_msg(chat_id, "⏳ Triggering cloud campaign...")
                    res = trigger_github_workflow()
                    send_telegram_msg(chat_id, res)

        except Exception as e:
            print(f"Error in polling loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
