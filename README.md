# RCB Ticket Monitor — Cloud Setup Guide

## Files in this folder
- `monitor.py` — the main script
- `requirements.txt` — Python dependencies
- `render.yaml` — Render deployment config

---

## Step-by-step deploy on Render (free, 10 minutes)

### Step 1 — Upload to GitHub
1. Go to https://github.com and create a free account if you don't have one
2. Click **New repository** → name it `rcb-monitor` → click **Create repository**
3. Upload all 3 files (monitor.py, requirements.txt, render.yaml) using the **"uploading an existing file"** link

### Step 2 — Deploy on Render
1. Go to https://render.com and sign up (free, use GitHub login)
2. Click **New** → **Blueprint**
3. Connect your GitHub account → select the `rcb-monitor` repo
4. Render auto-detects the render.yaml config → click **Apply**

### Step 3 — Set your Telegram credentials
In Render dashboard → your service → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID (e.g. 7544754206) |

Click **Save Changes** — the service restarts automatically.

### Step 4 — Confirm it's running
- Go to **Logs** tab in Render
- You should see: `RCB Ticket Monitor started 🔴`
- You'll receive a Telegram message: `✅ RCB Ticket Monitor is running!`

---

## That's it! 
The monitor runs 24/7 in the cloud. You'll get a Telegram alert the moment tickets appear on shop.royalchallengers.com — even with your phone off.
