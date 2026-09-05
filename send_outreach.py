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
        "subject": "Last-minute cancellations at {business_name}",
        "body": """Hi {business_name} team,

I'm one of the founders of a project called Fillo, and I was checking out your barbershop in {location}. Really love the brand you've built!

I'm reaching out to you directly because I've been talking to a lot of shop owners recently, and they all hate the exact same thing: last-minute cancellations. When a chair sits empty for an hour, that's lost revenue you just never get back.

We built Fillo specifically to fix this. When you get a sudden cancellation or have a quiet morning, you just tap one button on Fillo. It instantly creates a beautiful flash promo for your shop and broadcasts it directly to your clients on Telegram. 

Because it's on Telegram, 90%+ of your clients actually see it instantly (unlike Instagram where the algorithm hides it). They can book that empty slot directly through the app in seconds. No phone calls, no friction.

It runs completely in the background and doesn't replace your current booking system. 

Since we are expanding in {location}, I'd love to give you a full month completely free so you can see the extra revenue it brings in. No credit cards, no commitments. It takes 2 minutes to set up right here:
👉 Start your free trial: https://t.me/Filloappbot

Would you be open to testing it out this week?

Cheers,
The Fillo Team"""
    },
    "salon_spa": {
        "subject": "Filling empty slots at {business_name}",
        "body": """Hi {business_name} team,

I'm the founder of a project called Fillo. I came across your salon in {location} and really admire the experience you provide.

I'm reaching out because almost every salon owner I speak to deals with the same frustration: late cancellations and quiet mornings where therapists or stylists are sitting idle. That's just lost revenue for the business.

We built Fillo to solve exactly this. If a slot suddenly opens up, you tap one button. Fillo instantly generates a branded flash promo and sends it straight to your clients on Telegram. 

Since Telegram notifications go straight to their phones, 90%+ of your clients see it instantly. They can book the open slot directly from the message in seconds. No back-and-forth phone calls needed.

It doesn't replace your current software, it just sits alongside it to catch the revenue that usually slips through the cracks.

I'd love to give {business_name} a full month completely free to test it out. No credit cards, no commitments. Setup takes 2 minutes directly on Telegram:
👉 Start your free trial: https://t.me/Filloappbot

Let me know if you'd be open to trying it out!

Cheers,
The Fillo Team"""
    },
    "pilates": {
        "subject": "Empty reformer spots at {business_name}?",
        "body": """Hi {business_name} team,

I'm one of the founders of Fillo, and I was looking at your studio in {location}. Love your approach to training!

I wanted to reach out because we've noticed a massive pain point for studio owners: classes almost always have 1 or 2 empty spots due to late cancellations. When those spots go unfilled, it's lost revenue.

We built Fillo to fix this. When a class has an unexpected opening, you tap one button. Fillo automatically creates a branded promo for your studio and broadcasts it instantly to your member list on Telegram. 

Because it's Telegram, open rates are 90%+ (way higher than email). Your members see the alert instantly and can grab the open spot in seconds. 

It doesn't replace your main scheduling system—it just acts as a safety net to fill the empty spots your existing setup can't reach in time.

I'd love to offer your studio a full month completely free to see how much extra revenue it captures. No credit card required. You can set it up in 2 minutes right here:
👉 Start your free trial: https://t.me/Filloappbot

Would you be open to testing it this week?

Cheers,
The Fillo Team"""
    },
    "general": {
        "subject": "Quick question about {business_name}",
        "body": """Hi {business_name} team,

I'm the founder of a project called Fillo, and I was checking out your business in {location}. Really like what you guys are doing!

I'm reaching out because I've been talking to local business owners who all struggle with the same thing: quiet hours and last-minute cancellations. When you have downtime, it's just lost revenue.

We built Fillo to solve this. When things are slow, you tap one button. Fillo instantly generates a branded flash promo for {business_name} and sends it directly to your clients on Telegram. 

Because Telegram is instant, 90%+ of your clients see the message immediately, and they can book directly through the app in seconds. No friction, no marketing effort required on your end.

It works alongside whatever system you already use. I'd love to give you a full month completely free to see if it brings you extra bookings. No credit cards, no commitments. It takes about 2 minutes to set up:
👉 Start your free trial: https://t.me/Filloappbot

Let me know if you'd be open to testing it out!

Cheers,
The Fillo Team"""
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

# Follow-Up Email Template (Sent 3 days after Email #1 if no reply)
FOLLOWUP_TEMPLATE = {
    "subject": "Quick follow-up: {business_name}",
    "body": """Hi {business_name} team,

Quick bump on my previous email, wanted to make sure it didn't get buried!

We're currently offering local businesses in {location} a 1-month free trial of Fillo to fill quiet hours and last-minute cancellations (no credit card or software changes needed).

You can claim your free trial in under 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Would love to hear if you're open to trying it out this week!

Best,
The Fillo Team"""
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

    # Run Lead Cleaner & Bounce Verification before starting campaign
    try:
        from bounce_cleaner import run_lead_cleaning
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

    # Categorize leads for Initial Outreach
    pending_initial = []

    for lead in leads:
        email_addr = lead["Email"].strip()
        info = get_lead_info(state, email_addr)
        status = info.get("status")

        if status in ["bounced", "invalid_domain", "email_not_found", "sent"]:
            continue

        if status == "pending":
            pending_initial.append(lead)

    print(f"Pending Initial Outreach: {len(pending_initial)}")

    # Create work queue
    work_queue = []
    for l in pending_initial:
        work_queue.append((l, "initial"))

    if not work_queue:
        print("No outreach actions due at this time!")
        return

    # Telegram settings
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        print("Telegram notifications enabled.")

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

        # Real-time pre-send SMTP verification
        try:
            from bounce_cleaner import verify_email_inbox_smtp
            is_valid, reason = verify_email_inbox_smtp(recipient_email)
            if is_valid is False:
                msg = f"Skipped non-existent email address for {business_name} ({recipient_email}): {reason}"
                print(f"-> 🚫 {msg}")
                state[recipient_email] = {"status": "email_not_found", "reason": reason}
                save_state(state)
                continue
        except Exception as e:
            print(f"Pre-send SMTP check warning: {e}")

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
            server = None
            try:
                print("Connecting to Gmail SMTP server...")
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(sender_email, app_password)

                # Send email
                send_email(server, sender_email, recipient_email, subject, body)
                success_msg = f"[{tag}] Email successfully sent to {business_name} ({recipient_email})"
                print(f"-> {success_msg}")
                send_telegram_notification(tg_token, tg_chat_id, f"✅ {success_msg}")

                try:
                    server.quit()
                    server = None
                except Exception:
                    pass

                # Update rich state
                existing_info = get_lead_info(state, recipient_email)
                if action_type == "followup":
                    state[recipient_email] = {
                        "status": "sent",
                        "sent_at": existing_info.get("sent_at", now_ts),
                        "followup_status": "sent",
                        "followup_sent_at": time.time()
                    }
                else:
                    state[recipient_email] = {
                        "status": "sent",
                        "sent_at": time.time(),
                        "followup_status": "none"
                    }

                save_state(state)
                sent_count += 1
                
                # Delay before next email (mimic human behavior)
                if idx < len(work_queue) - 1 and sent_count < DAILY_LIMIT:
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
