#!/usr/bin/env python3
import os
import re
import json
import csv
import smtplib
import imaplib
import email
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "outreach_state.json")
CSV_FILE = os.path.join(BASE_DIR, "fillo_leads.csv")
CLEANED_CSV_FILE = os.path.join(BASE_DIR, "fillo_leads_clean.csv")

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "joinfillo@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "vfvqocxsqrxdpttf")
IMAP_SERVER = "imap.gmail.com"

def get_mx_server(domain):
    """Retrieve primary MX mail server for a domain."""
    if not domain or "." not in domain:
        return None
    try:
        out = subprocess.check_output(
            ["nslookup", "-type=MX", domain],
            stderr=subprocess.STDOUT,
            timeout=4
        ).decode()
        for line in out.splitlines():
            if "mail exchanger =" in line:
                return line.split("mail exchanger =")[-1].strip().split()[-1].rstrip(".")
    except Exception:
        pass
    return None

def verify_email_inbox_smtp(email_addr):
    """
    Performs real-time SMTP RCPT TO handshake to verify if an inbox actually exists.
    Returns:
      (True, "250 OK") if inbox exists and is active.
      (False, "550 Account does not exist") if inbox is NOT FOUND.
      (None, "Connection error / Timeout") if verification is inconclusive.
    """
    if not email_addr or "@" not in email_addr:
        return False, "Invalid email format"
        
    domain = email_addr.split("@")[-1].lower()
    mx = get_mx_server(domain)
    if not mx:
        return False, "No MX server found"

    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mx, 25)
        server.helo("gmail.com")
        server.mail("joinfillo@gmail.com")
        code, resp = server.rcpt(email_addr)
        server.quit()
        resp_str = resp.decode(errors="ignore").replace("\n", " ")
        if code == 250:
            return True, "250 OK (Inbox exists)"
        elif code in [550, 551, 552, 553, 554]:
            return False, f"SMTP Rejected ({code}): {resp_str[:80]}"
        else:
            return None, f"SMTP Response {code}: {resp_str[:80]}"
    except Exception as e:
        return None, str(e)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def scan_imap_bounces():
    """Scan IMAP inbox for all bounced email addresses."""
    if not SENDER_EMAIL or not APP_PASSWORD:
        return set()

    bounced_emails = set()
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(SENDER_EMAIL, APP_PASSWORD)
        mail.select("inbox")

        status, response = mail.search(None, "ALL")
        if status == "OK" and response[0]:
            mail_ids = response[0].split()
            for num in mail_ids:
                status, data = mail.fetch(num, '(RFC822)')
                if status != "OK":
                    continue
                msg = email.message_from_bytes(data[0][1])

                from_ = str(msg.get("From", "")).lower()
                subj_ = str(msg.get("Subject", "")).lower()

                if "mailer-daemon" in from_ or "postmaster" in from_ or "failure" in subj_ or "undelivered" in subj_ or "delivery status" in subj_:
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            payload = part.get_payload(decode=True)
                            if payload:
                                body += payload.decode(errors="ignore") + "\n"
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")

                    found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body)
                    for e in found:
                        e_clean = e.lower().strip()
                        if not any(domain_part in e_clean for domain_part in [
                            "joinfillo@gmail.com", "mailer-daemon", "postmaster", "googlemail.com",
                            "mx.google.com", "mail.gmail.com", "smtp.gmail.com"
                        ]):
                            bounced_emails.add(e_clean)

        mail.logout()
    except Exception as e:
        print(f"Error scanning IMAP bounces: {e}")

    return bounced_emails

def run_lead_cleaning():
    """
    1. Scans IMAP for past bounce notifications.
    2. Marks bounced emails as 'bounced' in state.
    3. Performs real-time SMTP RCPT TO verification on pending leads.
    4. Marks non-existent addresses as 'email_not_found'.
    5. Saves clean leads to fillo_leads_clean.csv.
    """
    state = load_state()
    bounced_from_imap = scan_imap_bounces()

    # Update state with IMAP bounces
    bounced_marked = 0
    for bounced_addr in bounced_from_imap:
        for key in list(state.keys()):
            if key.lower() == bounced_addr:
                if state[key] != "bounced":
                    state[key] = "bounced"
                    bounced_marked += 1
        if bounced_addr not in [k.lower() for k in state.keys()]:
            state[bounced_addr] = "bounced"
            bounced_marked += 1

    # Load CSV leads
    leads = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                leads.append(row)
    else:
        fieldnames = ["Business", "Email", "Category", "Location"]

    not_found_marked = 0
    clean_leads = []

    for lead in leads:
        email_addr = lead.get("Email", "").strip()
        if not email_addr:
            continue

        email_lower = email_addr.lower()

        # Check if already marked as bounced or invalid in state
        if state.get(email_addr) in ["bounced", "email_not_found", "invalid_domain"] or \
           state.get(email_lower) in ["bounced", "email_not_found", "invalid_domain"]:
            continue

        # If pending (not yet sent or verified), run real-time SMTP verification
        if state.get(email_addr) is None and state.get(email_lower) is None:
            is_valid, reason = verify_email_inbox_smtp(email_addr)
            if is_valid is False:
                state[email_addr] = "email_not_found"
                not_found_marked += 1
                print(f"🚫 [EMAIL NOT FOUND]: {email_addr} ({reason})")
                continue

        clean_leads.append(lead)

    save_state(state)

    # Save cleaned CSV file
    with open(CLEANED_CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_leads)

    total_leads = len(leads)
    sent_count = sum(1 for v in state.values() if v == "sent")
    bounced_count = sum(1 for v in state.values() if v in ["bounced", "email_not_found", "invalid_domain"])
    pending_valid = sum(1 for l in clean_leads if state.get(l.get("Email", "").strip()) is None)

    return {
        "total_leads": total_leads,
        "clean_leads_count": len(clean_leads),
        "sent_delivered": sent_count,
        "bounced_or_not_found": bounced_count,
        "pending_valid": pending_valid,
        "newly_bounced_marked": bounced_marked,
        "newly_not_found_marked": not_found_marked
    }

if __name__ == "__main__":
    print("Running Real-Time Fillo SMTP Lead Cleaner...")
    stats = run_lead_cleaning()
    print(json.dumps(stats, indent=4))
