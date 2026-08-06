#!/usr/bin/env python3
import os
import csv
import json
import time
import random
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==================== CONFIGURATION ====================
CSV_FILE_PATH = "fillo_leads.csv" if os.path.exists("fillo_leads.csv") else "/Users/mac/.gemini/antigravity/brain/56b36a84-f0a0-4300-a6db-4bcfbafc3216/fillo_leads.csv"
STATE_FILE_PATH = "outreach_state.json"

# Google Outreach Security Settings
raw_limit = os.environ.get("DAILY_LIMIT", "50")
DAILY_LIMIT = int(raw_limit) if raw_limit.strip() else 50  # Max emails to send per day (configurable via environment)
MIN_DELAY_SECS = 60       # Minimum delay between emails (1 minute)
MAX_DELAY_SECS = 180      # Maximum delay between emails (3 minutes)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# ========================================================

# Email templates: professional, benefit-driven, natural tone with direct Telegram Mini App link
TEMPLATES = {
    "barber": {
        "subject": "{business_name} — quick question",
        "body": """Hi there,

Do you ever have last-minute cancellations where the chair just sits empty?

We built Fillo for exactly this. When you have a free slot, one tap sends a flash alert to your clients on Telegram — they see it, they show up, the hour is filled.

No reservation system, no new software. Just a way to make sure your quiet hours don't stay quiet.

Free for the first month. Takes 2 minutes:
👉 https://t.me/Filloappbot

Worth a look?

— Fillo Team"""
    },
    "salon_spa": {
        "subject": "Quick question about {business_name}",
        "body": """Hi there,

When a therapist or stylist has a last-minute gap — what happens to that hour?

Fillo lets you fill it instantly. One tap sends a flash alert to your clients on Telegram — they see it and come in. No booking system, no back and forth.

Free for the first month. Takes 2 minutes:
👉 https://t.me/Filloappbot

— Fillo Team"""
    },
    "pilates": {
        "subject": "Empty spots at {business_name}?",
        "body": """Hi there,

Late cancellations are painful — instructor ready, studio open, spot just sitting empty.

Fillo fixes this. When a spot opens, you tap once. Your members on Telegram get a flash alert and show up to fill it.

Free for the first month. Takes 2 minutes:
👉 https://t.me/Filloappbot

— Fillo Team"""
    },
    "weedshop": {
        "subject": "Quick question about {business_name}",
        "body": """Hi there,

Do you have slow hours during the day where the shop is quiet?

Fillo lets you fill them instantly. One tap sends a flash alert to your existing customers on Telegram — they see it and come in.

No app to download, no booking system. Just a simple way to make sure your quiet hours don't stay quiet.

Free for the first month. Takes 2 minutes:
👉 https://t.me/Filloappbot

Worth a look?

— Fillo Team"""
    },
    "restaurant_cafe": {
        "subject": "Empty tables during quiet hours at {business_name}?",
        "body": """Hi there,

Slow afternoons, last-minute no-shows — every place deals with it.

Fillo lets you instantly alert your regulars on Telegram when you have empty tables. They see it, they come in. No booking platform, no commission fees.

Free for a month. Takes 2 minutes:
👉 https://t.me/Filloappbot

— Fillo Team"""
    },
    "general": {
        "subject": "Quick question about {business_name}",
        "body": """Hi there,

Do you have slow hours or last-minute gaps that go unfilled?

Fillo lets you alert your existing clients on Telegram in one tap — they see it, they show up, the hour is filled.

Free for one month. Setup takes 2 minutes:
👉 https://t.me/Filloappbot

— Fillo Team"""
    }
}

FOLLOWUP_TEMPLATE = {
    "subject": "Re: {business_name}",
    "body": """Hi,

Just bumping this up in case my last email got buried.

If empty hours are ever an issue, Fillo is worth 2 minutes of your time:
👉 https://t.me/Filloappbot

No pressure either way.

— Fillo Team"""
}


def load_state():
    if os.path.exists(STATE_FILE_PATH):
        try:
            with open(STATE_FILE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE_PATH, "w") as f:
        json.dump(state, f, indent=4)

def get_lead_info(state, email_addr):
    val = state.get(email_addr) or state.get(email_addr.lower())
    if isinstance(val, dict):
        return val
    elif isinstance(val, str):
        return {"status": val, "sent_at": 0, "followup": "none"}
    return {"status": "pending", "sent_at": 0, "followup": "none"}

def send_email(server, sender_email, recipient_email, subject, body):
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Fillo Team <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject
    
    # Custom headers to look like a standard, manual email
    msg["X-Mailer"] = "Gmail Outlook Client"
    msg["X-Priority"] = "3"
    
    # Plain text version
    text_part = MIMEText(body, "plain")
    msg.attach(text_part)
    
    # HTML version with open pixel and click tracking
    tracking_url = os.environ.get("TRACKING_BASE_URL", "https://fillo.app")
    try:
        from email_analytics import encode_email_token
        token = encode_email_token(recipient_email)
        open_pixel_url = f"{tracking_url}/track/open?id={token}"
        click_redirect_url = f"{tracking_url}/track/click?id={token}&target=https://t.me/Filloappbot"
        
        html_body = body.replace("\n", "<br>\n")
        html_body = html_body.replace("https://t.me/Filloappbot", f'<a href="{click_redirect_url}">https://t.me/Filloappbot</a>')
        html_body += f'<br><br><img src="{open_pixel_url}" width="1" height="1" style="display:none;" alt="" />'
        
        html_part = MIMEText(f"<html><body>{html_body}</body></html>", "html")
        msg.attach(html_part)
    except Exception as e:
        print(f"Tracking attachment warning: {e}")
        
    server.sendmail(sender_email, recipient_email, msg.as_string())

def send_telegram_notification(token, chat_id, text):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        import ssl
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=context) as response:
            pass
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")

def main():
    print("=======================================")
    print("      Fillo Automated Cold Outreach    ")
    print("=======================================\n")
    
    # Check environment variables first
    sender_email = os.environ.get("SENDER_EMAIL")
    if not sender_email:
        sender_email = input("Enter your custom or Google email (e.g. joinfillo@gmail.com): ").strip()
    else:
        print(f"Using sender email from environment: {sender_email}")
        
    if not sender_email:
        print("Email cannot be empty.")
        return
        
    app_password = os.environ.get("APP_PASSWORD")
    if not app_password:
        print("\n*NOTE: For Gmail, do NOT enter your regular password.")
        print("Go to your Google Account > Security > 2-Step Verification > App Passwords.")
        print("Generate a 16-character App Password for this script.")
        app_password = input("Enter your 16-character Google App Password: ").strip().replace(" ", "")
    else:
        app_password = app_password.replace(" ", "")
        print("Using App Password from environment.")
        
    if not app_password:
        print("App password cannot be empty.")
        return

    mode = os.environ.get("OUTREACH_MODE")
    if not mode:
        mode = input("\nChoose mode:\n 1. Dry Run (Simulates sending, doesn't send emails)\n 2. Live Send (Actually sends emails)\nChoice (1 or 2): ").strip()
    else:
        print(f"Using mode from environment: {mode}")
        
    is_dry_run = mode != "2"
    
    if is_dry_run:
        print("\n--- RUNNING IN DRY-RUN MODE (SIMULATION) ---")
    else:
        print("\n--- RUNNING IN LIVE SEND MODE ---")
        confirm = os.environ.get("CONFIRM_SEND")
        if not confirm:
            confirm = input("Are you sure you want to send real emails? (y/n): ").strip().lower()
        else:
            print(f"Using confirmation from environment: {confirm}")
            
        if confirm.strip().lower() != "y":
            print("Aborted.")
            return

    # Run Lead Cleaner & Bounce Verification before starting campaign
    try:
        from bounce_cleaner import run_lead_cleaning, check_mx_record
        print("Running pre-campaign lead cleaning & bounce verification...")
        clean_stats = run_lead_cleaning()
        print(f"Cleaner Stats: Clean Leads: {clean_stats['clean_leads_count']}, Bounced: {clean_stats['bounced']}, Pending Valid: {clean_stats['pending_valid']}")
    except Exception as e:
        print(f"Cleaner warning: {e}")
        def check_mx_record(d): return True

    # Load leads
    leads = []
    active_csv = "fillo_leads_clean.csv" if os.path.exists("fillo_leads_clean.csv") else CSV_FILE_PATH
    if not os.path.exists(active_csv):
        print(f"Error: Lead file not found at {active_csv}")
        return
        
    with open(active_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
            
    print(f"Loaded {len(leads)} leads from CSV.")
    
    state = load_state()
    now_ts = time.time()
    THREE_DAYS_SECS = 3 * 86400

    # Categorize leads into 3-Day Follow-Ups and Pending Initial Outreach
    due_followups = []
    pending_initial = []

    import datetime
    is_weekend = datetime.datetime.now().weekday() >= 5  # 5=Saturday, 6=Sunday

    for lead in leads:
        email_addr = lead["Email"].strip()
        info = get_lead_info(state, email_addr)
        status = info.get("status")
        followup_status = info.get("followup_status", info.get("followup", "none"))
        sent_at = info.get("sent_at", 0)

        if status in ["bounced", "invalid_domain", "email_not_found"]:
            continue

        if status == "sent":
            # FOLLOW-UPS ARE TEMPORARILY DISABLED PER USER REQUEST
            pass
        elif status == "pending":
            pending_initial.append(lead)

    print(f"Due 3-Day Follow-Ups: {len(due_followups)}")
    print(f"Pending Initial Outreach: {len(pending_initial)}")

    # Combine work: Process Follow-Ups first, then Pending Initial
    work_queue = []
    for l in due_followups:
        work_queue.append((l, "followup"))
    for l in pending_initial:
        work_queue.append((l, "initial"))

    if not work_queue:
        print("No outreach or follow-up actions due at this time!")
        return

    # Telegram settings
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        print("Telegram notifications enabled.")

    if not is_dry_run:
        print("Connecting to Gmail SMTP server...")
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(sender_email, app_password)
        except Exception as e:
            msg = f"Failed to connect to SMTP server: {e}"
            print(f"🚨 {msg}")
            send_telegram_notification(tg_token, tg_chat_id, f"🚨 {msg}")
            return

    sent_count = 0
    for idx, (lead, action_type) in enumerate(work_queue):
        if sent_count >= DAILY_LIMIT:
            msg = f"Daily safety limit of {DAILY_LIMIT} emails reached. Stopping outreach campaign."
            print(f"\n{msg}")
            send_telegram_notification(tg_token, tg_chat_id, f"🚨 {msg}")
            break

        business_name = lead["Business"]
        recipient_email = lead["Email"].strip()
        category = lead["Category"]
        location = lead["Location"]

        # Pre-send verification is disabled because GitHub Actions IPs are blocked by SpamHaus.
        # Emails are already verified when added to the leads pool.

        # Select template based on action type
        if action_type == "followup":
            subject = FOLLOWUP_TEMPLATE["subject"].format(business_name=business_name)
            body = FOLLOWUP_TEMPLATE["body"].format(business_name=business_name, location=location)
            tag = "🔄 3-DAY FOLLOW-UP"
        else:
            template = get_template(category)
            subject = template["subject"].format(business_name=business_name)
            body = template["body"].format(business_name=business_name, location=location)
            tag = "✉️ INITIAL OUTREACH"

        print(f"\n[{idx+1}/{len(work_queue)}] [{tag}] Processing: {business_name} ({recipient_email})")

        if is_dry_run:
            print(f"-> [DRY RUN] Would send [{action_type}] to: {recipient_email}")
            print(f"-> Subject: {subject}")
            print("-" * 40)
            sent_count += 1
        else:
            try:
                # Reconnect if connection was dropped
                try:
                    server.noop()
                except Exception:
                    print("Reconnecting to SMTP server...")
                    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                    server.starttls()
                    server.login(sender_email, app_password)
                
                # Send email
                send_email(server, sender_email, recipient_email, subject, body)
                success_msg = f"[{tag}] Email successfully sent to {business_name} ({recipient_email})"
                print(f"-> {success_msg}")
                send_telegram_notification(tg_token, tg_chat_id, f"✅ {success_msg}")

                # Update State
                now_ts = time.time()
                current_info = get_lead_info(state, recipient_email)
                if action_type == "followup":
                    state[recipient_email] = {
                        "status": "sent",
                        "sent_at": current_info.get("sent_at", now_ts),
                        "followup_status": "sent"
                    }
                else:
                    state[recipient_email] = {
                        "status": "sent",
                        "sent_at": now_ts,
                        "followup_status": "none"
                    }
                save_state(state)
                sent_count += 1
                
            except Exception as e:
                error_msg = f"Error sending to {business_name} ({recipient_email}): {e}"
                print(f"-> {error_msg}")
                send_telegram_notification(tg_token, tg_chat_id, f"❌ {error_msg}")
                # Sleep slightly on error to cool down
                time.sleep(10)
                
        # Delay before next email (mimic human behavior)
        if not is_dry_run and idx < len(work_queue) - 1 and sent_count < DAILY_LIMIT:
            delay = random.randint(MIN_DELAY_SECS, MAX_DELAY_SECS)
            print(f"-> Safety Delay: Waiting {delay} seconds before next send...")
            time.sleep(delay)

    if not is_dry_run and 'server' in locals() and server:
        try:
            server.quit()
        except Exception:
            pass

    print(f"\nSession complete. Total emails processed: {sent_count}")
    if not is_dry_run:
        print("State saved. You can run the script again tomorrow to process the next batch.")

if __name__ == "__main__":
    main()
