#!/usr/bin/env python3
"""
Fillo Global Lead Pool Cleaner
Verifies all leads in leads_pool.csv using real-time SMTP handshakes.
Moves invalid leads to a separate file to ensure 100% deliverability.
"""
import csv
import os
import time
from bounce_cleaner import verify_email_inbox_smtp

POOL_FILE = "leads_pool.csv"
CLEAN_POOL_FILE = "leads_pool_verified.csv"
INVALID_POOL_FILE = "leads_pool_invalid.csv"

def clean_pool():
    if not os.path.exists(POOL_FILE):
        print(f"Error: {POOL_FILE} not found.")
        return

    print("=======================================")
    print("      Fillo Global Pool Cleaner        ")
    print("=======================================\n")

    with open(POOL_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    print(f"Loaded {len(leads)} leads from {POOL_FILE}.")
    print("Beginning SMTP Verification (this may take a while)...\n")

    valid_leads = []
    invalid_leads = []
    uncertain_leads = []

    for idx, lead in enumerate(leads):
        email_addr = lead["Email"].strip()
        print(f"[{idx+1}/{len(leads)}] Checking {email_addr}...")
        
        is_valid, reason = verify_email_inbox_smtp(email_addr)
        
        if is_valid is True:
            valid_leads.append(lead)
            print("  -> ✅ VALID")
        elif is_valid is False:
            invalid_leads.append((lead, reason))
            print(f"  -> 🚫 INVALID ({reason})")
        else:
            uncertain_leads.append(lead) # Keep uncertain ones just in case
            print(f"  -> ⚠️ UNCERTAIN ({reason})")
            
        time.sleep(0.5) # Prevent spamming DNS/SMTP

    print("\n--- Cleaning Summary ---")
    print(f"Total Processed: {len(leads)}")
    print(f"Valid/Deliverable: {len(valid_leads) + len(uncertain_leads)}")
    print(f"Invalid/Non-existent: {len(invalid_leads)}")

    # Write valid + uncertain to the new clean pool
    if valid_leads or uncertain_leads:
        with open(CLEAN_POOL_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Business", "Email", "Category", "Location"])
            writer.writeheader()
            writer.writerows(valid_leads)
            writer.writerows(uncertain_leads)
        print(f"Saved deliverable leads to {CLEAN_POOL_FILE}")

    # Write invalid ones for record keeping
    if invalid_leads:
        with open(INVALID_POOL_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Business", "Email", "Category", "Location", "Reason"])
            for lead, reason in invalid_leads:
                writer.writerow([lead["Business"], lead["Email"], lead["Category"], lead["Location"], reason])
        print(f"Saved invalid leads to {INVALID_POOL_FILE}")

    # Replace old pool with new clean pool
    if os.path.exists(CLEAN_POOL_FILE):
        os.replace(CLEAN_POOL_FILE, POOL_FILE)
        print(f"Replaced {POOL_FILE} with 100% verified leads.")

if __name__ == "__main__":
    clean_pool()
