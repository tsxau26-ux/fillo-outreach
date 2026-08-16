#!/usr/bin/env python3
import os
import csv

# Configuration
POOL_FILE = "leads_pool.csv"
LEADS_FILE = "fillo_leads.csv"
REFILL_COUNT = 50

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

    if len(new_leads) < REFILL_COUNT:
        print("Not enough new leads available to refill. The pool is running low.")
        print("Auto-triggering the lead generator to replenish the pool...")
        
        import random
        from lead_generator import generate_leads
        
        niches = ["Spa", "Barbershop", "Pilates", "Restaurant", "Cafe", "Nail Salon", "Hair Salon"]
        locations = ["Dubai", "Abu Dhabi", "London", "Manchester", "New York", "Los Angeles", "Chicago", "Miami", "Toronto"]
        
        target_niche = random.choice(niches)
        target_location = random.choice(locations)
        
        try:
            generate_leads(target_niche, target_location, limit=40)
        except Exception as e:
            print(f"Failed to auto-generate leads: {e}")
            
        # Reload the pool after generation
        new_leads = []
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row["Email"].strip().lower()
                if email not in existing_emails:
                    new_leads.append(row)
                    
        print(f"Found {len(new_leads)} fresh leads available after auto-replenishment.")

    if not new_leads:
        print("Still no new leads available after generation attempt. Aborting refill.")
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
