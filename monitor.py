import os
import requests
import sys

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
RCB_URL   = "https://shop.royalchallengers.com"
KEYWORDS  = ["book now", "buy tickets", "available", "add to cart", "select seats"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
    data = r.json()
    if data.get("ok"):
        print("✅ Telegram alert sent!")
    else:
        print(f"❌ Telegram error: {data.get('description')}")

def fetch_page():
    try:
        r = requests.get(RCB_URL, headers=HEADERS, timeout=15)
        if r.ok and len(r.text) > 500:
            print(f"✅ Fetch success ({len(r.text)//1024} KB)")
            return r.text.lower()
    except Exception as e:
        print(f"Direct fetch failed: {e}")
    return None

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing secrets!")
        sys.exit(1)

    print(f"🔍 Checking {RCB_URL}...")
    html = fetch_page()

    if not html:
        print("⚠ Could not fetch page.")
        sys.exit(0)

    sold_out = any(x in html for x in ["sold out", "sold-out", "no tickets"])
    found    = [k for k in KEYWORDS if k in html]

    if found and not sold_out:
        print(f"🔴 TICKETS FOUND! {found}")
        send_telegram(
            "🔴 RCB TICKETS ALERT!\n\n"
            "Tickets are available NOW!\n\n"
            "👉 Book NOW: https://shop.royalchallengers.com\n\n"
            "⚡ Move fast — they sell out in minutes!"
        )
    else:
        print("ℹ No tickets found yet.")

if __name__ == "__main__":
    main()
