#!/usr/bin/env python3
import os
import csv
import time
from apify_client import ApifyClient
from bounce_cleaner import verify_email_inbox_smtp

# Setup APIFY TOKEN
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
POOL_FILE = "leads_pool.csv"

def get_category_from_query(query):
    query_lower = query.lower()
    if "barber" in query_lower:
        return "Barber"
    elif any(word in query_lower for word in ["spa", "salon", "nail", "hair"]):
        return "Salon"
    elif "pilates" in query_lower or "yoga" in query_lower or "fitness" in query_lower:
        return "Pilates"
    elif any(word in query_lower for word in ["restaurant", "cafe", "food", "dining", "bar"]):
        return "Restaurant/Cafe"
    else:
        return "General"

def generate_leads(query, location, limit=20):
    print(f"=======================================")
    print(f"      Fillo Lead Generator Engine      ")
    print(f"=======================================\n")
    print(f"🔍 Searching Google Maps for: '{query} in {location}' (Target: {limit} places)")
    
    client = ApifyClient(APIFY_TOKEN)
    
    # Official Apify Google Maps Scraper
    run_input = {
        "searchStringsArray": [f"{query} in {location}"],
        "maxCrawledPlacesPerSearch": limit,
        "language": "en",
        "extractEmailsAndContacts": True,
    }

    print("⏳ Starting Apify Scraper... (This may take a few minutes)")
    try:
        run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    except Exception as e:
        print(f"❌ Failed to run Apify actor: {e}")
        return

    print("✅ Scraping complete! Fetching results...")
    
    category = get_category_from_query(query)
    new_leads = []
    
    for item in client.dataset(run.default_dataset_id).iterate_items():
        business_name = item.get("title", "")
        # Emails are usually returned in a list or within phoneAndEmail
        emails = item.get("emails", [])
        if not emails and item.get("email"):
            emails = [item.get("email")]
            
        if not emails:
            continue
            
        # Get the first valid email
        target_email = emails[0].strip()
        
        # Verify the email with SMTP check before adding it!
        print(f"Verifying: {target_email} for {business_name}...")
        is_valid, reason = verify_email_inbox_smtp(target_email)
        
        if is_valid is True:
            print(f"  -> ✅ VALID: Added to pool!")
            new_leads.append({
                "Business": business_name,
                "Email": target_email,
                "Category": category,
                "Location": location
            })
        else:
            print(f"  -> 🚫 INVALID ({reason}): Discarded.")
            
    if not new_leads:
        print("\nNo verified leads were found in this batch. Try a different search term.")
        return
        
    print(f"\n🎉 Successfully found and verified {len(new_leads)} highly-targeted leads!")
    
    # Append to leads_pool.csv
    file_exists = os.path.exists(POOL_FILE)
    with open(POOL_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Business", "Email", "Category", "Location"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_leads)
        
    print(f"✅ Leads added to {POOL_FILE} safely.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 lead_generator.py <search_query> <location> [limit]")
        print("Example: python3 lead_generator.py 'Barbershop' 'Tunis' 20")
        sys.exit(1)
        
    q = sys.argv[1]
    loc = sys.argv[2]
    l = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    generate_leads(q, loc, l)
