from lead_generator import generate_leads
import os
os.environ["APIFY_TOKEN"] = "REMOVED_TOKEN"
try:
    generate_leads("Spa", "London", limit=5)
except Exception as e:
    print("Error:", e)
