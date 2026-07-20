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
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", 50))  # Max emails to send per day (configurable via environment)
MIN_DELAY_SECS = 60       # Minimum delay between emails (1 minute)
MAX_DELAY_SECS = 180      # Maximum delay between emails (3 minutes)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# ========================================================

# Templates tailored to Fillo's Telegram features
TEMPLATES = {
    "barber": {
        "subject": "question about empty slots at {business_name}",
        "body": """Hi {business_name} team,

I came across your barbershop in {location} and love the premium setup you have.

We built a tool called Fillo that helps barbershops fill empty chairs and last-minute cancellations. When you have a cancellation, you can notify your clients instantly on Telegram with a direct booking link to grab the chair.

Most shops see open spots filled within an hour of sending the Telegram notification.

Are you open to a brief chat this week to see how it works?

Best regards,

Fillo Team"""
    },
    "salon_spa": {
        "subject": "question about empty slots at {business_name}",
        "body": """Hi {business_name} team,

I came across your salon and love the work you do.

We built a tool called Fillo that helps salons and spas turn quiet hours and cancellations into paid bookings. When you have an empty slot, the app lets you alert your clients instantly on Telegram with a direct booking link to claim the spot.

Most salons see open slots booked within an hour of sending the Telegram notification.

Are you open to a brief chat this week to see how it works?

Best regards,

Fillo Team"""
    },
    "pilates": {
        "subject": "question about empty slots at {business_name}",
        "body": """Hi {business_name} team,

I came across your pilates studio in {location} and love your focus on quality training.

We built a tool called Fillo that helps pilates and fitness studios fill last-minute open reformer spots or cancellations. When a slot opens up, the app lets you alert your clients instantly on Telegram with a direct booking link.

Most studios see open spots filled within an hour of sending the notification.

Are you open to a brief chat this week to see how it works?

Best regards,

Fillo Team"""
    },
    "general": {
        "subject": "question about empty slots at {business_name}",
        "body": """Hi {business_name} team,

I came across your business in {location} and love what you do.

We built a tool called Fillo that helps hospitality and booking-based businesses turn quiet hours and last-minute open slots into paid bookings. When you have slow periods, the app lets you alert your clients instantly on Telegram with a direct link.

Most businesses see new bookings within an hour of sending the notification.

Are you open to a brief chat this week to see how it works?

Best regards,

Fillo Team"""
    }
}

def get_template(category):
    cat_lower = category.lower()
    if "barber" in cat_lower:
        return TEMPLATES["barber"]
    elif any(word in cat_lower for word in ["spa", "salon", "nail"]):
        return TEMPLATES["salon_spa"]
    elif "pilates" in cat_lower:
        return TEMPLATES["pilates"]
    else:
        return TEMPLATES["general"]

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

def send_email(server, sender_email, recipient_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = f"Fillo Team <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject
    
    # Custom headers to look like a standard, manual email
    msg["X-Mailer"] = "Gmail Outlook Client"
    msg["X-Priority"] = "3"
    
    msg.attach(MIMEText(body, "plain"))
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

    # Load leads
    leads = []
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Error: Lead file not found at {CSV_FILE_PATH}")
        return
        
    with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
            
    print(f"Loaded {len(leads)} leads from CSV.")
    
    state = load_state()
    
    # Filter out already sent leads
    pending_leads = [l for l in leads if state.get(l["Email"]) != "sent"]
    print(f"Pending leads to send: {len(pending_leads)}")
    
    if not pending_leads:
        print("All leads have already been emailed!")
        return
        
    # Telegram settings
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        print("Telegram notifications enabled.")

    sent_count = 0
    for idx, lead in enumerate(pending_leads):
        if sent_count >= DAILY_LIMIT:
            msg = f"Daily safety limit of {DAILY_LIMIT} emails reached. Stopping outreach campaign."
            print(f"\n{msg}")
            send_telegram_notification(tg_token, tg_chat_id, f"🚨 {msg}")
            break
            
        business_name = lead["Business"]
        recipient_email = lead["Email"]
        category = lead["Category"]
        location = lead["Location"]
        
        # Select and customize template
        template = get_template(category)
        subject = template["subject"].format(business_name=business_name)
        body = template["body"].format(business_name=business_name, location=location)
        
        print(f"\n[{idx+1}/{len(pending_leads)}] Processing: {business_name} ({recipient_email})")
        
        if is_dry_run:
            print(f"-> [DRY RUN] Would send to: {recipient_email}")
            print(f"-> Subject: {subject}")
            print("-" * 40)
            sent_count += 1
        else:
            server = None
            try:
                # Connect on demand
                print("Connecting to Gmail SMTP server...")
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(sender_email, app_password)
                
                # Send email
                send_email(server, sender_email, recipient_email, subject, body)
                success_msg = f"Email successfully sent to {business_name} ({recipient_email})"
                print(f"-> {success_msg}")
                send_telegram_notification(tg_token, tg_chat_id, f"✅ {success_msg}")
                
                # Disconnect
                try:
                    server.quit()
                    server = None
                except Exception:
                    pass
                
                # Update state
                state[recipient_email] = "sent"
                save_state(state)
                sent_count += 1
                
                # Delay before next email (mimic human behavior)
                if idx < len(pending_leads) - 1 and sent_count < DAILY_LIMIT:
                    delay = random.randint(MIN_DELAY_SECS, MAX_DELAY_SECS)
                    print(f"-> Safety Delay: Waiting {delay} seconds (mimicking human typing) before the next send...")
                    time.sleep(delay)
            except Exception as e:
                error_msg = f"Error sending to {business_name} ({recipient_email}): {e}"
                print(f"-> {error_msg}")
                send_telegram_notification(tg_token, tg_chat_id, f"❌ {error_msg}")
                if server:
                    try:
                        server.quit()
                    except Exception:
                        pass
                # Sleep slightly on error to cool down
                time.sleep(10)
                
    print(f"\nSession complete. Total emails processed: {sent_count}")
    if not is_dry_run:
        print("State saved. You can run the script again tomorrow to process the next batch.")

if __name__ == "__main__":
    main()
