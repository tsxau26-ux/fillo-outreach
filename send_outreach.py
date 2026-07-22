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

# Templates tailored to Fillo's Telegram & Promo Generation features
TEMPLATES = {
    "barber": {
        "subject": "Fill empty chairs & launch promos at {business_name} (1 Month Free Trial)",
        "body": """Hi {business_name} team,

I came across your barbershop in {location} and love the quality of your work.

We built Fillo — an automated marketing and revenue tool designed specifically for local stores and barbershops to fill quiet hours and last-minute cancellations.

Here is how Fillo works for {business_name}:
1. Whenever you have empty chairs or slow hours, you can create and launch local promotions in 1 click right inside Fillo.
2. Fillo automatically generates branded promo graphics & QR codes and broadcasts instant booking alerts directly to your clients on Telegram.
3. You get 90%+ open rates compared to regular emails or manual Instagram posts.

Key Benefits for your shop:
• Zero out lost revenue from last-minute no-shows.
• Launch instant local ads & flash sales without paying marketing agencies.
• Works seamlessly alongside your current setup in under 5 minutes.

We are currently offering select shops in {location} a 1-Month FREE Trial (100% risk-free, no credit card required) so you can test it and start filling empty chairs immediately.

Would you be open to claiming your 1-month free trial this week?

Best regards,

Fillo Team"""
    },
    "salon_spa": {
        "subject": "Turn cancellations into paid bookings at {business_name} (1 Month Free Trial)",
        "body": """Hi {business_name} team,

I came across your salon/spa and loved your work.

We built Fillo — an automated revenue recovery tool designed specifically for beauty salons and spas to turn quiet hours and cancellations into paid bookings.

Here is how Fillo works for {business_name}:
1. Whenever a slot opens up or you have slow hours, you can launch local flash promos in 1 click right inside Fillo.
2. Fillo automatically generates custom promo visuals & QR codes and alerts your loyal client list directly on Telegram.
3. Clients book open slots instantly through a direct link.

Key Benefits for {business_name}:
• Keep your therapists & stylists fully booked every day.
• Launch local promotions effortlessly without technical skills or marketing agencies.
• 0 friction — works alongside your current booking system in 5 minutes.

We are offering local salons a 1-Month FREE Trial (completely risk-free, no credit card needed) to help you keep your schedule full.

Would you be open to claiming your 1-month free trial this week?

Best regards,

Fillo Team"""
    },
    "pilates": {
        "subject": "Fill empty reformer slots & launch promos at {business_name} (1 Month Free Trial)",
        "body": """Hi {business_name} team,

I came across your studio in {location} and love your focus on quality training.

We built Fillo — an automated revenue tool designed specifically for fitness and pilates studios to fill empty reformer slots and class cancellations.

Here is how Fillo works for {business_name}:
1. When a class has open spots or slow hours, you can launch a local promotion in 1 click right inside Fillo.
2. Fillo automatically generates branded promo assets & QR codes and broadcasts instant reservation alerts directly to your members on Telegram.
3. Members grab remaining spots in seconds.

Key Benefits:
• Maximize class occupancy and eliminate lost revenue from cancellations.
• Effortlessly generate and launch local offers without complex ad platforms.
• 100% complementary to your current booking system.

We are currently offering select studios in {location} a 1-Month FREE Trial (risk-free, zero commitment) so you can test it live.

Would you be open to claiming your 1-month free trial this week?

Best regards,

Fillo Team"""
    },
    "general": {
        "subject": "Fill quiet hours & launch local promos at {business_name} (1 Month Free Trial)",
        "body": """Hi {business_name} team,

I came across your business in {location} and love what you do.

We built Fillo — an automated marketing and revenue platform that helps local stores and service businesses turn slow hours and empty slots into paid bookings.

Here is how Fillo works for {business_name}:
1. Whenever you have slow periods, you can launch local promotions and flash offers in 1 click right inside Fillo.
2. Fillo automatically generates branded promo graphics & QR codes and broadcasts instant alerts directly to your clients on Telegram.
3. You achieve instant 90%+ engagement and fast bookings.

Key Benefits for {business_name}:
• Fill quiet hours and recover lost revenue automatically.
• Launch instant promotions without hiring expensive marketing agencies.
• 0 hassle — sets up in under 5 minutes alongside your current setup.

We are currently offering select businesses in {location} a 1-Month FREE Trial (completely risk-free, no credit card required) to test it live.

Would you be open to claiming your 1-month free trial this week?

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
