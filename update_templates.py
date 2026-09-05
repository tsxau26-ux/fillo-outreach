import re

with open("send_outreach.py", "r") as f:
    content = f.read()

new_templates = '''TEMPLATES = {
    "barber": {
        "subject": "Free for 1 month: fill empty chairs at {business_name}",
        "body": """Hi {business_name} team,

I noticed your barbershop in {location} and really like the work you put into your craft.

I'm reaching out because we built something called Fillo that solves a problem every shop deals with: last-minute cancellations and quiet hours where chairs sit empty.

Here's what Fillo does for you:
- When you have an open slot, you tap one button inside Fillo.
- Fillo generates a branded promo for your shop automatically (visuals, QR code, booking link).
- That promo goes straight to your clients on Telegram, where it gets 90%+ open rates (way higher than email or Instagram).
- Clients book the slot directly. No calls, no back-and-forth.

You don't need to change anything about how you currently manage appointments. Fillo just fills the gaps.

We're offering {business_name} a free 1-month trial (no credit card, no commitment, cancel anytime). Setup takes about 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Would you be open to trying it out this week?

Best,
The Fillo Team"""
    },
    "salon_spa": {
        "subject": "Free for 1 month: fill cancelled slots at {business_name}",
        "body": """Hi {business_name} team,

I came across your salon and really admire the experience you've built for your clients.

Quick question: how do you currently handle last-minute cancellations or quiet mornings when therapists and stylists are free?

We built Fillo specifically for this. When a slot opens up, you tap one button and Fillo takes care of the rest:
- It generates a branded flash promo with your salon's name (visuals, QR code, and a direct booking link).
- That promo goes instantly to your clients on Telegram, where open rates are 90%+ (compared to ~20% for email).
- Clients book the open slot directly. No phone calls needed.

It works alongside your existing setup. Nothing to change, nothing to learn.

We're offering {business_name} a free 1-month trial (no credit card, no commitment, cancel anytime). Setup takes about 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Want to give it a try?

Best,
The Fillo Team"""
    },
    "pilates": {
        "subject": "Free for 1 month: fill empty reformer spots at {business_name}",
        "body": """Hi {business_name} team,

I found your studio in {location} and love your approach to training.

One thing we've heard from studio owners is that reformer classes rarely run at full capacity: there's almost always a spot or two that goes unfilled, especially from late cancellations.

That's exactly what Fillo solves:
- When a class has open spots, you tap one button in Fillo.
- Fillo automatically generates a branded promo for your studio (visuals, QR code, and a direct reservation link).
- That promo is sent instantly to your member list on Telegram, where 90%+ of people actually see it.
- Members grab the spot in seconds. Done.

It doesn't replace your scheduling system: it just fills the empty spots your existing setup can't reach in time.

We're offering studios in {location} a free 1-month trial. No credit card, no commitment. Setup takes about 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Worth a look?

Best,
The Fillo Team"""
    },
    "weedshop": {
        "subject": "Free for 1 month: fill quiet hours at {business_name}",
        "body": """Hi {business_name} team,

I noticed your shop in {location} and wanted to reach out.

I'm getting in touch because we built a tool called Fillo that helps local shops deal with slow afternoons and quiet hours during the week.

Here's how Fillo helps:
- When you have a slow period, you tap one button inside Fillo.
- Fillo automatically creates a branded flash promo for {business_name} (graphics, QR code, and a direct link).
- That promo goes straight to your regular customers on Telegram, where open rates are 90%+ (much higher than email or social media).
- Customers see it and come in. No friction.

It works right alongside your current setup. Nothing to change, nothing to learn.

We're offering {business_name} a free 1-month trial (no credit card, no commitment, cancel anytime). Setup takes about 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Would you be open to trying it out this week?

Best,
The Fillo Team"""
    },
    "restaurant_cafe": {
        "subject": "Free for 1 month: fill empty tables at {business_name}",
        "body": """Hi {business_name} team,

I came across your place in {location} and really love the atmosphere you've created.

I wanted to reach out because we built a tool called Fillo that solves a problem almost every restaurant and cafe deals with: slow afternoons, last-minute cancellations, and empty tables during quiet hours.

Here's how Fillo helps:
- When you have a slow period or empty tables, you tap one button inside Fillo.
- Fillo automatically creates a branded flash promo for {business_name} (graphics, QR code, and a direct booking link).
- That promo goes straight to your regular customers on Telegram, where open rates are 90%+ (much higher than email or social media).
- Customers book the table directly. No friction.

It works right alongside your current reservation system. Nothing to change, nothing to learn.

We're offering {business_name} a free 1-month trial (no credit card, no commitment, cancel anytime). Setup takes about 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Would you be open to trying it out this week?

Best,
The Fillo Team"""
    },
    "general": {
        "subject": "Free for 1 month: fill quiet hours at {business_name}",
        "body": """Hi {business_name} team,

I came across your business in {location} and like what you've built.

I wanted to reach out because we created a tool called Fillo that helps local businesses like yours turn slow hours into paid bookings without any marketing effort on your part.

Here's how it works:
- When you have a quiet period, you tap one button inside Fillo.
- Fillo automatically creates a branded promo for {business_name} (graphics, QR code, and a direct booking link).
- That promo goes straight to your clients on Telegram, where open rates are 90%+ (much higher than email or social posts).
- Clients book directly. No friction.

You don't need to change anything about how you currently do business. Fillo just gives you a way to monetize downtime.

We're offering {business_name} a free 1-month trial (no credit card, no commitment, cancel anytime). Setup takes about 2 minutes directly on Telegram:
👉 Start your free trial here: https://t.me/Filloappbot

Open to trying it out?

Best,
The Fillo Team"""
    }
}

FOLLOWUP_TEMPLATE = {
    "subject": "Quick follow-up: {business_name}",
    "body": """Hi {business_name} team,

Quick bump on my previous email, wanted to make sure it didn't get buried!

We're currently offering local businesses in {location} a 1-month free trial of Fillo to fill quiet hours and last-minute cancellations (no credit card or software changes needed).

Takes 2 minutes to set up directly on Telegram:
👉 https://t.me/Filloappbot

No pressure either way.

Best,
The Fillo Team"""
}'''

# Replace everything from TEMPLATES = { to the end of FOLLOWUP_TEMPLATE
import re
pattern = re.compile(r"TEMPLATES = \{.*?\n\}\n\nFOLLOWUP_TEMPLATE = \{.*?\n\}", re.DOTALL)
new_content = pattern.sub(new_templates, content)

with open("send_outreach.py", "w") as f:
    f.write(new_content)

print("Done replacing templates.")
