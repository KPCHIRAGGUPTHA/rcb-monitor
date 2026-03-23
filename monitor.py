import os
import time
import requests
import logging
from datetime import datetime

# ── Config from environment variables ──────────────────────────────────────
BOT_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID     = os.environ.get("TELEGRAM_CHAT_ID", "")
INTERVAL    = int(os.environ.get("CHECK_INTERVAL", "60"))   # seconds
KEYWORDS    = os.environ.get("KEYWORDS", "book now,buy tickets,available,add to cart").split(",")
RCB_URL     = "https://shop.royalchallengers.com"

# ── Logging setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ── Proxy list (tries each in order) ───────────────────────────────────────
def get_proxies(url):
    return [
        f"https://corsproxy.io/?{requests.utils.quote(url)}",
        f"https://api.allorigins.win/get?url={requests.utils.quote(url)}",
        f"https://api.codetabs.com/v1/proxy?quest={requests.utils.quote(url)}",
    ]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Fetch page content ──────────────────────────────────────────────────────
def fetch_page():
    # First try direct request
    try:
        r = requests.get(RCB_URL, headers=HEADERS, timeout=15)
        if r.ok and len(r.text) > 500:
            log.info(f"Direct fetch success ({len(r.text)//1024} KB)")
            return r.text.lower()
    except Exception as e:
        log.warning(f"Direct fetch failed: {e}")

    # Fallback to proxies
    for i, proxy_url in enumerate(get_proxies(RCB_URL), 1):
        try:
            r = requests.get(proxy_url, headers=HEADERS, timeout=15)
            if not r.ok:
                raise Exception(f"HTTP {r.status_code}")
            # allorigins returns JSON
            if "allorigins" in proxy_url:
                html = r.json().get("contents", "")
            else:
                html = r.text
            if html and len(html) > 500:
                log.info(f"Proxy {i} success ({len(html)//1024} KB)")
                return html.lower()
            raise Exception("Empty response")
        except Exception as e:
            log.warning(f"Proxy {i} failed: {e}")

    return None

# ── Send Telegram message ───────────────────────────────────────────────────
def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        log.error("Telegram credentials not set! Check environment variables.")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
        data = r.json()
        if data.get("ok"):
            log.info("✅ Telegram alert sent!")
            return True
        else:
            log.error(f"Telegram error: {data.get('description')}")
            return False
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False

# ── Check for tickets ───────────────────────────────────────────────────────
def check_tickets():
    log.info(f"Checking {RCB_URL} ...")
    html = fetch_page()

    if not html:
        log.warning("All fetch methods failed. Will retry next interval.")
        return False

    sold_out = any(x in html for x in ["sold out", "sold-out", "no tickets"])
    found = [k.strip() for k in KEYWORDS if k.strip().lower() in html]

    if found and not sold_out:
        log.info(f"🔴 TICKETS FOUND! Keywords: {found}")
        return True
    elif sold_out:
        log.info("Page loaded. Status: Sold out.")
    else:
        log.info(f"Page OK. No ticket keywords found yet. (Keywords watched: {[k.strip() for k in KEYWORDS]})")
    return False

# ── Keep Render free tier alive (prevents spin-down) ───────────────────────
def ping_self():
    self_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if self_url:
        try:
            requests.get(self_url, timeout=10)
        except:
            pass

# ── Main loop ───────────────────────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("RCB Ticket Monitor started 🔴")
    log.info(f"Checking every {INTERVAL} seconds")
    log.info(f"Keywords: {[k.strip() for k in KEYWORDS]}")
    log.info("=" * 50)

    # Validate credentials on startup
    if not BOT_TOKEN or not CHAT_ID:
        log.error("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set!")
        log.error("Set them as environment variables on Render.")
        return

    # Send startup message
    send_telegram("✅ RCB Ticket Monitor is running!\nI'll alert you the moment tickets go on sale. #PlayBold 🔴")

    alert_sent = False
    check_count = 0

    while True:
        check_count += 1
        log.info(f"--- Check #{check_count} ---")

        try:
            tickets_found = check_tickets()

            if tickets_found and not alert_sent:
                alert_sent = True
                msg = (
                    "🔴 RCB TICKETS ALERT!\n\n"
                    "Tickets appear to be available on the RCB website!\n\n"
                    "👉 Book NOW: https://shop.royalchallengers.com\n\n"
                    "⚡ Move fast — they sell out in minutes!"
                )
                send_telegram(msg)

            # Reset alert if page goes back to unavailable
            if not tickets_found and alert_sent:
                alert_sent = False
                log.info("Alert reset — tickets no longer detected.")

        except Exception as e:
            log.error(f"Unexpected error during check: {e}")

        # Ping self every 10 checks to prevent Render free tier spin-down
        if check_count % 10 == 0:
            ping_self()

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
