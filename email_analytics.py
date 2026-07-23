#!/usr/bin/env python3
"""
Fillo Email Analytics Engine
Tracks email opens, clicks, and engagement rates for cold outreach campaigns.
"""
import os
import json
import time
import base64
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_FILE = os.path.join(BASE_DIR, "email_analytics.json")
STATE_FILE = os.path.join(BASE_DIR, "outreach_state.json")

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8827856631:AAGTJvC7UkOqVHtTEgbV4WxK_Ir8kE0IDAQ")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5219669099")

# Transparent 1x1 GIF image bytes (35 bytes)
PIXEL_GIF_BASE64 = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
PIXEL_GIF_BYTES = base64.b64decode(PIXEL_GIF_BASE64)

def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"opens": {}, "clicks": {}, "events": []}
    return {"opens": {}, "clicks": {}, "events": []}

def save_analytics(data):
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def send_telegram_alert(text):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        import ssl
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=ctx) as resp:
            pass
    except Exception as e:
        print(f"Telegram alert error: {e}")

def encode_email_token(email_addr):
    return base64.urlsafe_b64encode(email_addr.encode()).decode().rstrip("=")

def decode_email_token(token):
    try:
        padding = "=" * (4 - (len(token) % 4))
        return base64.urlsafe_b64decode((token + padding).encode()).decode()
    except Exception:
        return token

def record_open_event(email_addr, ip="Unknown", user_agent="Unknown"):
    analytics = load_analytics()
    email_clean = email_addr.lower().strip()
    now_ts = time.time()
    
    opens = analytics.setdefault("opens", {})
    email_data = opens.setdefault(email_clean, {"count": 0, "first_open": now_ts, "last_open": now_ts, "history": []})
    
    is_first = email_data["count"] == 0
    email_data["count"] += 1
    email_data["last_open"] = now_ts
    email_data["history"].append({"ts": now_ts, "ip": ip, "ua": user_agent})
    
    analytics["events"].append({
        "type": "open",
        "email": email_clean,
        "ts": now_ts,
        "ip": ip,
        "ua": user_agent
    })
    
    save_analytics(analytics)
    
    if is_first:
        alert_msg = f"👀 **EMAIL OPENED!**\n\nRecipient: `{email_clean}`\nOpened for the 1st time!"
    else:
        alert_msg = f"👀 **EMAIL RE-OPENED!**\n\nRecipient: `{email_clean}`\nTotal Opens: {email_data['count']}"
    
    print(f"Recorded open for {email_clean} (Count: {email_data['count']})")
    send_telegram_alert(alert_msg)

def record_click_event(email_addr, target_url="https://t.me/Filloappbot"):
    analytics = load_analytics()
    email_clean = email_addr.lower().strip()
    now_ts = time.time()
    
    clicks = analytics.setdefault("clicks", {})
    email_data = clicks.setdefault(email_clean, {"count": 0, "first_click": now_ts, "last_click": now_ts, "url": target_url})
    
    email_data["count"] += 1
    email_data["last_click"] = now_ts
    
    analytics["events"].append({
        "type": "click",
        "email": email_clean,
        "url": target_url,
        "ts": now_ts
    })
    
    save_analytics(analytics)
    
    alert_msg = f"🔥 **LINK CLICKED!**\n\nRecipient: `{email_clean}`\nClicked Telegram Link -> `{target_url}`!"
    print(f"Recorded click for {email_clean}")
    send_telegram_alert(alert_msg)

def get_analytics_report():
    analytics = load_analytics()
    
    # Load sent emails from state
    sent_count = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                sent_count = sum(1 for v in state.values() if (v == "sent" or (isinstance(v, dict) and v.get("status") == "sent")))
        except Exception:
            pass
            
    opens_dict = analytics.get("opens", {})
    clicks_dict = analytics.get("clicks", {})
    
    unique_opens = len(opens_dict)
    total_open_views = sum(data.get("count", 0) for data in opens_dict.values())
    unique_clicks = len(clicks_dict)
    
    open_rate = (unique_opens / sent_count * 100) if sent_count > 0 else 0
    click_rate = (unique_clicks / sent_count * 100) if sent_count > 0 else 0
    
    report = f"""📈 **Fillo Email Analytics Report**

• **Total Delivered Emails:** {sent_count}
• **Unique Recipients Opened:** {unique_opens} ({open_rate:.1f}% Open Rate)
• **Total Email Views:** {total_open_views}
• **Unique Telegram Clicks:** {unique_clicks} ({click_rate:.1f}% Click Rate)

Recent Opens:"""

    if opens_dict:
        sorted_opens = sorted(opens_dict.items(), key=lambda x: x[1].get("last_open", 0), reverse=True)[:5]
        for e, data in sorted_opens:
            count = data.get("count", 1)
            report += f"\n  - `{e}` ({count} view{'s' if count > 1 else ''})"
    else:
        report += "\n  (No opens recorded yet)"
        
    return report

if __name__ == "__main__":
    print(get_analytics_report())
