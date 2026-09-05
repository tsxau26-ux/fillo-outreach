import re

with open("send_outreach.py", "r") as f:
    text = f.read()

# Define the new templates block
new_templates_code = '''TEMPLATES = {
    "barber": {
        "subject": "Last-minute cancellations at {business_name}",
        "body": """Hi {business_name} team,

I'm reaching out to you directly because I've been talking to a lot of shop owners recently, and they all hate the exact same thing: last-minute cancellations. When a chair sits empty, that's just lost money you can't get back.

I'm the founder of Fillo, a new tool built specifically to fix this. When you have an unexpected empty chair, you tap one button on your phone. Fillo instantly generates a branded flash-discount for {business_name} and sends it directly to your clients on Telegram. 

Because Telegram is instant, your clients see it immediately and can grab the open slot in seconds. No friction, no marketing effort required on your end.

I'm giving local shops in {location} a full month completely free to prove it works. No credit cards, no commitments. It takes about 2 minutes to set up:
👉 Start your free trial: https://t.me/Filloappbot

Would love to hear if you're open to testing it out!

Best,
The Fillo Team"""
    },
    "salon_spa": {
        "subject": "Filling empty appointments at {business_name}",
        "body": """Hi {business_name} team,

I'm reaching out to you directly because I've been talking to a lot of salon and spa owners recently, and they all hate the exact same thing: last-minute cancellations and quiet hours. When an appointment goes unfilled, that's lost revenue.

I'm the founder of Fillo, a new tool built specifically to fix this. When you have unexpected downtime, you tap one button. Fillo instantly generates a branded flash-promo for {business_name} and sends it directly to your clients on Telegram. 

Because Telegram is instant, your clients see it immediately and can book the open slot in seconds. It works alongside your existing booking system seamlessly.

I'm giving local businesses in {location} a full month completely free to prove it works. No credit cards, no commitments. It takes about 2 minutes to set up:
👉 Start your free trial: https://t.me/Filloappbot

Let me know if you'd be open to testing it out!

Best,
The Fillo Team"""
    },
    "pilates": {
        "subject": "Empty reformer spots at {business_name}?",
        "body": """Hi {business_name} team,

I'm reaching out to you directly because I've been talking to studio owners recently, and they all struggle with the exact same thing: classes running with empty mats or reformers. 

I'm the founder of Fillo, a new tool built specifically to fill those empty spots. When you have a class that isn't full, you tap one button. Fillo instantly generates a branded last-minute drop-in promo for {business_name} and sends it directly to your clients on Telegram. 

Because Telegram is instant, your clients see it immediately and can grab the spot in seconds. It's the easiest way to maximize revenue per class with zero marketing effort.

I'm giving studios in {location} a full month completely free to prove it works. No credit cards, no commitments. It takes about 2 minutes to set up:
👉 Start your free trial: https://t.me/Filloappbot

Would love to hear if you're open to testing it out!

Best,
The Fillo Team"""
    },
    "f_and_b": {
        "subject": "Empty tables at {business_name}",
        "body": """Hi {business_name} team,

I'm reaching out because I've been talking to a lot of restaurant and cafe owners recently, and they all struggle with the same thing: quiet hours and dead periods. When tables are sitting empty, that's just lost revenue.

I'm the founder of Fillo, a new tool built specifically to drive foot traffic during those slow hours. When things get quiet, you tap one button. Fillo instantly generates a branded flash-promo for {business_name} (like a 2-hour happy hour special) and sends it directly to your regular customers on Telegram. 

Because Telegram is instant, your customers see the push notification immediately and can reserve a table or drop by. It brings people through the door exactly when you need them.

I'm giving local spots in {location} a full month completely free to prove it works. No credit cards, no commitments. It takes about 2 minutes to set up:
👉 Start your free trial: https://t.me/Filloappbot

Let me know if you'd be open to testing it out!

Best,
The Fillo Team"""
    },
    "clinic": {
        "subject": "Last-minute cancellations at {business_name}",
        "body": """Hi {business_name} team,

I'm reaching out because I've been talking to clinic and practice managers recently, and they all hate the exact same thing: last-minute cancellations and no-shows. 

I'm the founder of Fillo, a new tool built specifically to recover that lost revenue. When a patient cancels unexpectedly, you tap one button. Fillo instantly generates a branded alert for the newly available slot at {business_name} and sends it directly to your waitlist/patients on Telegram. 

Because Telegram is instant, patients see the notification immediately and can claim the appointment in seconds. 

I'm giving clinics in {location} a full month completely free to prove it works. No credit cards, no commitments. It takes about 2 minutes to set up:
👉 Start your free trial: https://t.me/Filloappbot

Let me know if you'd be open to testing it out this week!

Best,
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
    elif any(word in cat_lower for word in ["restaurant", "cafe", "coffee", "dining", "food"]):
        return TEMPLATES["f_and_b"]
    elif any(word in cat_lower for word in ["clinic", "medspa", "chiropractor", "massage", "medical", "dental"]):
        return TEMPLATES["clinic"]
    elif any(word in cat_lower for word in ["spa", "salon", "nail", "tattoo"]):
        return TEMPLATES["salon_spa"]
    elif any(word in cat_lower for word in ["pilates", "gym", "fitness", "yoga"]):
        return TEMPLATES["pilates"]
    else:
        return TEMPLATES["general"]'''

# Regex to replace the entire TEMPLATES dict and get_template function
pattern = re.compile(r'TEMPLATES = \{.*?\n\s+return TEMPLATES\["general"\]', re.DOTALL)
new_text = pattern.sub(new_templates_code, text)

# Also remove the FOLLOWUP_TEMPLATE block since it's dead code
pattern2 = re.compile(r'\n# Follow-Up Email Template.*?\n\}\n', re.DOTALL)
new_text = pattern2.sub('\n', new_text)

with open("send_outreach.py", "w") as f:
    f.write(new_text)

