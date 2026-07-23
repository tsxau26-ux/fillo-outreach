#!/usr/bin/env python3
import os
import re
import json
import csv
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

def check_mx_record(domain):
    """Verify if a domain has valid MX DNS records."""
    if not domain or "." not in domain:
        return False
    try:
        out = subprocess.check_output(
            ["nslookup", "-type=MX", domain],
            stderr=subprocess.STDOUT,
            timeout=4
        ).decode()
        return "mail exchanger" in out.lower() or "mx" in out.lower()
    except Exception:
        return False

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
    1. Scans IMAP for bounce notifications.
    2. Marks bounced emails as 'bounced' in state.
    3. Performs MX domain validation on all pending leads.
    4. Filters fillo_leads.csv to create a clean, verified leads list.
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
        # Also ensure bounced_addr is recorded in state
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

    invalid_mx_marked = 0
    clean_leads = []

    for lead in leads:
        email_addr = lead.get("Email", "").strip()
        if not email_addr:
            continue

        email_lower = email_addr.lower()
        domain = email_lower.split("@")[-1] if "@" in email_lower else ""

        # Check if already marked as bounced in state
        if state.get(email_addr) == "bounced" or state.get(email_lower) == "bounced":
            continue

        # Check MX record if not yet processed
        if state.get(email_addr) is None and state.get(email_lower) is None:
            if not check_mx_record(domain):
                state[email_addr] = "invalid_domain"
                invalid_mx_marked += 1
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
    bounced_count = sum(1 for v in state.values() if v == "bounced")
    invalid_mx_count = sum(1 for v in state.values() if v == "invalid_domain")
    pending_valid = sum(1 for l in clean_leads if state.get(l.get("Email", "").strip()) is None)

    return {
        "total_leads": total_leads,
        "clean_leads_count": len(clean_leads),
        "sent_delivered": sent_count,
        "bounced": bounced_count,
        "invalid_mx": invalid_mx_count,
        "pending_valid": pending_valid,
        "newly_bounced_marked": bounced_marked,
        "newly_invalid_mx_marked": invalid_mx_marked
    }

if __name__ == "__main__":
    print("Running Fillo Lead Cleaner & Bounce Verification...")
    stats = run_lead_cleaning()
    print(json.dumps(stats, indent=4))
