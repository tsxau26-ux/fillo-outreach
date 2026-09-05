import json
import csv

state = {}
try:
    with open("outreach_state.json", "r") as f:
        state = json.load(f)
except Exception:
    pass

def get_lead_info(state, email_addr):
    val = state.get(email_addr) or state.get(email_addr.lower())
    if isinstance(val, dict):
        return val
    elif isinstance(val, str):
        return {"status": val, "sent_at": 0, "followup": "none"}
    return {"status": "pending", "sent_at": 0, "followup": "none"}

leads = []
with open("fillo_leads_clean.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        leads.append(row)

pending_initial = []
for lead in leads:
    email_addr = lead["Email"].strip()
    info = get_lead_info(state, email_addr)
    if info.get("status") == "pending":
        pending_initial.append(lead)

print(f"Total leads: {len(leads)}")
print(f"Pending leads: {len(pending_initial)}")
