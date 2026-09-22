#!/usr/bin/env python3
import os
import csv

# Configuration
POOL_FILE = "leads_pool.csv"
LEADS_FILE = "fillo_leads.csv"
RESERVE_FILE = "leads_reserve.csv"   # hand-verified spare tank, drained before paying Apify
REFILL_COUNT = 50


def alert(text):
    """Ping the owner on Telegram. Silent if no token/chat id is configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    print(text)
    if not token or not chat_id:
        return
    import ssl
    import urllib.request
    import urllib.parse
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=15)
    except Exception as e:
        print(f"Telegram alert failed: {e}")

def load_existing_emails(leads_file):
    emails = set()
    if os.path.exists(leads_file):
        try:
            with open(leads_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    emails.add(row["Email"].strip().lower())
        except Exception as e:
            print(f"Error loading existing leads: {e}")
    return emails

def main():
    print("=======================================")
    print("      Fillo Daily Lead Auto-Refill     ")
    print("=======================================\n")

    if not os.path.exists(POOL_FILE):
        print(f"Error: Pool file '{POOL_FILE}' not found.")
        return

    # Load existing emails to avoid duplicates
    existing_emails = load_existing_emails(LEADS_FILE)
    print(f"Found {len(existing_emails)} existing email leads in '{LEADS_FILE}'.")

    # Read the pool
    new_leads = []
    with open(POOL_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row["Email"].strip().lower()
            if email not in existing_emails:
                new_leads.append(row)

    print(f"Found {len(new_leads)} fresh leads available in the pool.")

    # Spare tank: hand-verified leads. Drain these before paying Apify for more.
    reserve_taken = []
    if len(new_leads) < REFILL_COUNT and os.path.exists(RESERVE_FILE):
        batch_emails = {l["Email"].strip().lower() for l in new_leads}
        taken, kept = [], []
        with open(RESERVE_FILE, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                email = row.get("Email", "").strip().lower()
                if not email or email in existing_emails or email in batch_emails:
                    continue  # already in the system; drop it from the reserve
                if len(new_leads) + len(taken) < REFILL_COUNT:
                    taken.append(row)
                else:
                    kept.append(row)
        if taken:
            reserve_taken = taken
            new_leads.extend(taken)
            with open(RESERVE_FILE, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["Business", "Email", "Category", "Location"])
                writer.writeheader()
                for row in kept:
                    writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
            print(f"Took {len(taken)} lead(s) from the reserve. {len(kept)} left in reserve.")

    if len(new_leads) < REFILL_COUNT:
        print("Not enough new leads available to refill. The pool is running low.")
        print("Auto-triggering the lead generator to replenish the pool...")
        
        import random
        try:
            from lead_generator import generate_leads
        except Exception as e:
            # Never let an import problem kill the whole run before sending.
            alert(f"🚨 Fillo refill: lead generator could not load ({e}). Sending continues with the leads already in the list.")
            generate_leads = None

        niches = [
            # 70% Food & Beverage (Top Priority)
            "Restaurant", "Coffee Shop", "Cafe", "Fine Dining", "Bar", "Pub", "Bistro", "Cocktail Bar",
            "Restaurant", "Coffee Shop", "Cafe", "Fine Dining", "Bar", "Pub", "Bistro", "Cocktail Bar",
            # 30% Other High-Value Niches (No Nails/Spas)
            "Aesthetics Clinic", "Dental Clinic", "Chiropractor", "Physiotherapy",
            "High-end Barbershop", "Luxury Hair Salon", "Boutique Gym", "Pilates Studio"
        ]
        locations = [
            # Asia
            "Tokyo", "Singapore", "Hong Kong", "Bangkok", "Kuala Lumpur", "Seoul", "Taipei",
            # Europe
            "London", "Paris", "Berlin", "Rome", "Madrid", "Amsterdam", "Stockholm", "Dublin", "Manchester",
            # North America (US/Canada)
            "New York", "Los Angeles", "Chicago", "Miami", "San Francisco", "Austin", "Toronto", "Vancouver", "Montreal"
        ]
        
        target_niche = random.choice(niches)
        target_location = random.choice(locations)
        
        if not os.environ.get("APIFY_TOKEN"):
            alert("🚨 Fillo refill: APIFY_TOKEN is missing, so no new leads can be found. Add it in GitHub repo Settings > Secrets and variables > Actions.")
        try:
            if generate_leads:
                generate_leads(target_niche, target_location, limit=40)
        except Exception as e:
            alert(f"🚨 Fillo refill: lead finder failed for '{target_niche} in {target_location}'.\nReason: {e}")
            
        # Reload the pool after generation. Keep what the reserve already gave us:
        # rebuilding this list from the pool alone would silently drop those leads.
        new_leads = list(reserve_taken)
        seen = {l["Email"].strip().lower() for l in new_leads}
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row["Email"].strip().lower()
                if email not in existing_emails and email not in seen:
                    new_leads.append(row)
                    seen.add(email)

        print(f"Found {len(new_leads)} fresh leads available after auto-replenishment "
              f"({len(reserve_taken)} of them from the reserve).")

    if not new_leads:
        alert("⚠️ Fillo refill: no new leads found, so the send list did not grow. "
              "Check the Apify account (key valid? credit left?).")
        return

    # Pick the next 50 (or less if not enough)
    batch_to_add = new_leads[:REFILL_COUNT]
    print(f"Refilling batch of {len(batch_to_add)} leads...")

    # Write to target leads file (append)
    file_exists = os.path.exists(LEADS_FILE)
    with open(LEADS_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Business", "Email", "Category", "Location"])
        
        for lead in batch_to_add:
            writer.writerow([
                lead["Business"],
                lead["Email"],
                lead["Category"],
                lead["Location"]
            ])

    print(f"Successfully added {len(batch_to_add)} new leads to '{LEADS_FILE}'.")

if __name__ == "__main__":
    main()
