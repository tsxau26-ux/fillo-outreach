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

# Email templates. Short, plain text, no links: the only ask is a reply to
# this email. Signed by the team, never a person. No Telegram anywhere.
_CLOSE = """The first month is free, and we'll help you set it up. It takes about 5 minutes.

Interested? Just reply "yes" to this email and we'll send you the details.

The Fillo Team"""

TEMPLATES = {
    "barber": {
        "subject": "empty chairs at {business_name}",
        "body": """Hi {business_name} team,

When a client cancels last minute, does that chair just stay empty?

Fillo helps you fill it. You post the free slot in 3 taps. Your customers get an alert on their phone and book it.

""" + _CLOSE,
    },
    "salon_spa": {
        "subject": "last-minute cancellations at {business_name}",
        "body": """Hi {business_name} team,

When a client cancels last minute, does that appointment just go to waste?

Fillo helps you fill it. You post the free slot in 3 taps. Your customers get an alert on their phone and book it.

""" + _CLOSE,
    },
    "clinic": {
        "subject": "empty appointments at {business_name}",
        "body": """Hi {business_name} team,

When a patient cancels last minute, does that appointment just stay empty?

Fillo helps you fill it. You post the free slot in 3 taps. People who follow {business_name} get an alert on their phone and book it.

""" + _CLOSE,
    },
    "fitness": {
        "subject": "empty spots in your classes at {business_name}",
        "body": """Hi {business_name} team,

Do some classes at {business_name} run with empty spots?

Fillo helps you fill them. You post the open spots in 3 taps, like a drop-in deal for tonight's class. Your members get an alert on their phone and book.

""" + _CLOSE,
    },
    "f_and_b": {
        "subject": "quiet hours at {business_name}",
        "body": """Hi {business_name} team,

Are there hours when {business_name} is quiet and the tables sit empty?

Fillo helps you fill them. When it's slow, you post a quick deal in 3 taps, like "2-for-1 coffee until 4 pm". Customers who follow you get an alert on their phone and come in.

""" + _CLOSE,
    },
    "general": {
        "subject": "quiet hours at {business_name}",
        "body": """Hi {business_name} team,

Do you have quiet hours or last-minute cancellations at {business_name}?

Fillo helps you fill them. When it's slow, you post a deal in 3 taps. Customers who follow you get an alert on their phone and come in or book.

""" + _CLOSE,
    },
}

# Follow-ups stand on their own: older leads got a different first email.
FOLLOWUPS = {
    1: {
        "subject": "{business_name} + Fillo",
        "body": """Hi {business_name} team,

A quick follow-up. Fillo helps local businesses turn empty slots and quiet hours into paying customers. You post a deal in 3 taps, and your customers get it on their phone.

The first month is free, and we'll help you set it up.

Should we send you the details? A one-word reply is enough.

The Fillo Team""",
    },
    2: {
        "subject": "last note for {business_name}",
        "body": """Hi {business_name} team,

This is our last email. We don't want to fill your inbox.

If empty slots or quiet hours ever cost you money, just reply "Fillo" and we'll set you up with a free month.

Wishing you a busy season,
The Fillo Team""",
    },
}

# Days to wait: follow-up 1 after the first email, follow-up 2 after follow-up 1.
FOLLOWUP_GAPS_DAYS = {1: 3, 2: 4}
DAY_SECS = 86400


def get_template(category):
    cat_lower = category.lower()
    if "barber" in cat_lower:
        return TEMPLATES["barber"]
    elif any(word in cat_lower for word in ["restaurant", "cafe", "café", "coffee", "dining", "food", "bar", "pub",
                                            "bistro", "bakery", "tea", "juice", "ice cream", "lounge"]):
        return TEMPLATES["f_and_b"]
    elif any(word in cat_lower for word in ["clinic", "medspa", "chiropractor", "medical", "dental", "dentist",
                                            "physio"]):
        return TEMPLATES["clinic"]
    elif any(word in cat_lower for word in ["spa", "salon", "nail", "tattoo", "beauty", "massage", "hair"]):
        return TEMPLATES["salon_spa"]
    elif any(word in cat_lower for word in ["pilates", "gym", "fitness", "yoga", "studio"]):
        return TEMPLATES["fitness"]
    else:
        return TEMPLATES["general"]


def render_email(lead, action):
    """(subject, body) for one lead, footer not included."""
    if action == "followup1":
        template = FOLLOWUPS[1]
    elif action == "followup2":
        template = FOLLOWUPS[2]
    else:
        template = get_template(lead.get("Category", ""))
    values = {"business_name": lead["Business"], "location": lead.get("Location", "")}
    return template["subject"].format(**values), template["body"].format(**values)


# Shared mailbox providers: a reply from someone@gmail.com says nothing about
# another gmail.com lead. Matched on the first label (hotmail.fr, yahoo.co.th).
SHARED_PROVIDERS = {"gmail", "googlemail", "yahoo", "ymail", "hotmail", "outlook", "live", "msn",
                    "icloud", "me", "mac", "aol", "proton", "protonmail", "gmx", "yandex", "mail",
                    "zoho", "qq", "163", "naver"}


def has_replied(email_addr, replied_emails, replied_domains):
    """True if this lead, or a colleague on the same business domain, wrote to us."""
    addr = email_addr.strip().lower()
    if addr in replied_emails:
        return True
    domain = addr.rsplit("@", 1)[-1]
    return domain in replied_domains and domain.split(".")[0] not in SHARED_PROVIDERS


def followup_step(info):
    """How many follow-ups this lead already got: 0, 1 or 2."""
    return {"sent": 1, "done": 2}.get(info.get("followup_status"), 0)


def build_work_queue(leads, state, now, limit, replied=(set(), set())):
    """Today's sends: new leads plus follow-ups that are due.

    replied=None means the inbox could not be checked, so no follow-ups go out.
    While new leads wait, follow-ups take at most half the day.
    """
    new, due, seen = [], [], set()
    for lead in leads:
        addr = lead["Email"].strip()
        if addr.lower() in seen:
            continue
        seen.add(addr.lower())
        info = get_lead_info(state, addr)
        status = info.get("status")
        if status == "pending":
            new.append((lead, "initial"))
            continue
        if status != "sent" or replied is None or info.get("replied") or has_replied(addr, *replied):
            continue
        step = followup_step(info)
        if step == 0:
            last = info.get("sent_at")
        elif step == 1:
            last = info.get("followup_sent_at")
        else:
            continue
        if last and now - last >= FOLLOWUP_GAPS_DAYS[step + 1] * DAY_SECS:
            due.append((lead, f"followup{step + 1}"))

    follow = due[: (limit // 2 if new else limit)]
    fresh = new[: limit - len(follow)]
    queue = []
    for i in range(max(len(follow), len(fresh))):
        queue.extend(pair[i] for pair in (fresh, follow) if i < len(pair))
    return queue


BOUNCE_FROM = ("mailer-daemon", "postmaster")


def fetch_replied(sender_email, app_password):
    """Every address (and business domain) that ever wrote to the sender.

    Read-only: messages are not marked as read. Returns None on any failure,
    which turns follow-ups off for the run.
    """
    import imaplib
    from email.utils import parseaddr
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender_email, app_password)
        # "All Mail" is renamed in non-English Gmail; find it by its \\All flag.
        folder = "INBOX"
        status, boxes = mail.list()
        for box in boxes or []:
            line = box.decode("utf-8", "ignore") if isinstance(box, bytes) else str(box)
            if "\\All" in line:
                folder = line.rsplit(' "/" ', 1)[-1]
                break
        status, _ = mail.select(folder, readonly=True)
        if status != "OK":
            return None
        status, data = mail.search(None, "NOT", "FROM", sender_email)
        if status != "OK":
            return None
        ids = data[0].split()
        emails = set()
        for i in range(0, len(ids), 200):
            chunk = b",".join(ids[i:i + 200])
            status, rows = mail.fetch(chunk, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
            if status != "OK":
                return None
            for row in rows:
                if isinstance(row, tuple):
                    addr = parseaddr(row[1].decode("utf-8", "ignore").split(":", 1)[-1].strip())[1].lower()
                    if addr and "@" in addr and not addr.startswith(BOUNCE_FROM):
                        emails.add(addr)
        mail.logout()
        return emails, {a.rsplit("@", 1)[1] for a in emails}
    except Exception as e:
        print(f"Could not read the inbox for replies ({e}). Follow-ups are off for this run.")
        return None


# A Gmail account that keeps sending to dead addresses gets throttled, then
# blocked. Stopping early costs a day; a blocked account costs everything.
BOUNCE_LIMIT = 0.08
BOUNCE_WINDOW_DAYS = 14
BOUNCE_MIN_SAMPLE = 25
# Errors that mean "stop now", not "try the next address".
FATAL_SMTP = ("535", "534", "username and password not accepted", "5.4.5",
              "daily user sending limit exceeded", "account has been disabled",
              "5.7.0", "quota exceeded", "too many login attempts")
MAX_CONSECUTIVE_FAILURES = 5


def recent_bounce_rate(state, days=BOUNCE_WINDOW_DAYS):
    """Bounce rate over recent sends. Only rows carrying a date can count."""
    cutoff = time.time() - days * 86400
    sent = bounced = 0
    for value in state.values():
        if not isinstance(value, dict):
            continue
        stamp = value.get("sent_at") or value.get("bounced_at")
        if not stamp or stamp < cutoff:
            continue
        if value.get("status") == "sent":
            sent += 1
        elif value.get("status") == "bounced":
            bounced += 1
    total = sent + bounced
    return (bounced / total if total else 0.0), total


def email_footer():
    """Opt-out line + postal address. US CAN-SPAM requires both in a commercial email."""
    out = "\n\n--\nNot interested? Reply \"no thanks\" and we won't write again.\n"
    addr = os.environ.get("SENDER_POSTAL_ADDRESS", "").strip()
    if addr:
        out += addr + "\n"
    else:
        print("WARNING: SENDER_POSTAL_ADDRESS is not set. US law (CAN-SPAM) asks for a postal address in every commercial email.")
    return out


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
        print(f"Cleaner Stats: Clean Leads: {clean_stats['clean_leads_count']}, Bounced/not found: {clean_stats['bounced_or_not_found']}, Pending Valid: {clean_stats['pending_valid']}")
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

    # Warn while there is still time to act, not on the day it runs dry.
    low_water = DAILY_LIMIT * 2
    if 0 < len(pending_initial) < low_water:
        warn = (f"⚠️ Fillo outreach: {len(pending_initial)} leads left. "
                f"That is under 2 days at {DAILY_LIMIT}/day. Top up the list.")
        print(warn)
        send_telegram_notification(os.environ.get("TELEGRAM_BOT_TOKEN"),
                                   os.environ.get("TELEGRAM_CHAT_ID"), warn)

    # Who already wrote back: they get no follow-up, ever.
    replied = fetch_replied(sender_email, app_password)
    if replied is not None:
        for lead in leads:
            addr = lead["Email"].strip()
            info = state.get(addr)
            if isinstance(info, dict) and info.get("status") == "sent" and has_replied(addr, *replied):
                info["replied"] = True
        save_state(state)
        print(f"Inbox checked: {len(replied[0])} address(es) have written to us.")

    # Create work queue: new leads + follow-ups that are due
    work_queue = build_work_queue(leads, state, now_ts, DAILY_LIMIT, replied)
    followups_due = sum(1 for _, a in work_queue if a != "initial")
    print(f"Today's queue: {len(work_queue) - followups_due} first email(s), {followups_due} follow-up(s).")

    if not work_queue:
        msg = ("🚨 Fillo outreach: nothing to send today.\n"
               f"The list holds {len(leads)} addresses: every one is contacted, followed up, replied or marked bad.\n"
               "Add new leads to restart sending.")
        print(msg)
        send_telegram_notification(os.environ.get("TELEGRAM_BOT_TOKEN"),
                                   os.environ.get("TELEGRAM_CHAT_ID"), msg)
        # Fail loudly: a green run with 0 emails is what hid this for two weeks.
        raise SystemExit(1)

    # Telegram settings
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        print("Telegram notifications enabled.")

    # Guard the sender account: too many bounces and Gmail starts blocking.
    rate, sample = recent_bounce_rate(state)
    print(f"Recent bounce rate: {rate:.0%} of {sample} dated send(s) in the last {BOUNCE_WINDOW_DAYS} days.")
    if sample >= BOUNCE_MIN_SAMPLE and rate > BOUNCE_LIMIT:
        msg = (f"🛑 Fillo outreach: PAUSED, nothing sent.\n"
               f"{rate:.0%} of the last {sample} emails bounced (limit {BOUNCE_LIMIT:.0%}).\n"
               f"Sending more from {sender_email} now risks the account being blocked. "
               f"Clean the list before the next run.")
        print(msg)
        send_telegram_notification(tg_token, tg_chat_id, msg)
        raise SystemExit(1)

    sent_count = 0
    consecutive_failures = 0
    for idx, (lead, action_type) in enumerate(work_queue):
        if sent_count >= DAILY_LIMIT:
            msg = f"Daily safety limit of {DAILY_LIMIT} emails reached. Stopping outreach campaign."
            print(f"\n{msg}")
            send_telegram_notification(tg_token, tg_chat_id, f"🚨 {msg}")
            break

        business_name = lead["Business"]
        recipient_email = lead["Email"].strip()

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
        subject, body = render_email(lead, action_type)
        tag = {"followup1": "🔄 FOLLOW-UP 1", "followup2": "🔄 FOLLOW-UP 2"}.get(action_type, "✉️ INITIAL OUTREACH")

        body = body + email_footer()

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
                if action_type in ("followup1", "followup2"):
                    state[recipient_email] = dict(
                        existing_info,
                        status="sent",
                        followup_status="sent" if action_type == "followup1" else "done",
                        followup_sent_at=time.time(),
                    )
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

                # Some errors mean the account itself is in trouble. Grinding
                # through 50 more attempts makes that worse, not better.
                text = str(e).lower()
                if any(sig in text for sig in FATAL_SMTP):
                    stop = (f"🛑 Fillo outreach: STOPPED after {sent_count} email(s).\n"
                            f"Gmail refused the account: {e}\n"
                            f"That is a login or sending-limit problem, not a bad address. "
                            f"Check {sender_email} before the next run.")
                    print(stop)
                    send_telegram_notification(tg_token, tg_chat_id, stop)
                    save_state(state)
                    raise SystemExit(1)

                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    stop = (f"🛑 Fillo outreach: STOPPED after {sent_count} email(s). "
                            f"{consecutive_failures} sends failed in a row. Last error: {e}")
                    print(stop)
                    send_telegram_notification(tg_token, tg_chat_id, stop)
                    save_state(state)
                    raise SystemExit(1)

                # Sleep slightly on error to cool down
                time.sleep(10)
                
    print(f"\nSession complete. Total emails processed: {sent_count}")
    if not is_dry_run:
        print("State saved. You can run the script again tomorrow to process the next batch.")

        # Daily wrap-up: one message a day so silence means something is wrong.
        left = sum(1 for lead in leads
                   if get_lead_info(state, lead["Email"].strip()).get("status") == "pending")
        rate, sample = recent_bounce_rate(state)
        days_left = left / DAILY_LIMIT if DAILY_LIMIT else 0
        followups_note = ("" if replied is not None
                          else "⚠️ Follow-ups OFF: could not read the inbox to check replies.\n")
        summary = (f"📊 Fillo outreach, run finished.\n"
                   f"Sent now: {sent_count} (queue had {followups_due} follow-up(s))\n"
                   f"{followups_note}"
                   f"Leads left: {left} (about {days_left:.1f} day(s) at {DAILY_LIMIT}/day)\n"
                   f"Bounces, last {BOUNCE_WINDOW_DAYS} days: {rate:.0%} of {sample}")
        print(summary)
        send_telegram_notification(tg_token, tg_chat_id, summary)

if __name__ == "__main__":
    main()
