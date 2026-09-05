#!/usr/bin/env bash

cd "/Users/mac/Mounir-Email-System" || exit

export SENDER_EMAIL="joinfillo@gmail.com"
export APP_PASSWORD="vfvqocxsqrxdpttf"
export TELEGRAM_BOT_TOKEN="8827856631:AAGKFE3QPS2O1a_oSu0l8Nt71iuKAt8vgYY"
export TELEGRAM_CHAT_ID="5219669099"
export OUTREACH_MODE="2"
export DAILY_LIMIT="100"
export CONFIRM_SEND="y"
export APIFY_TOKEN="" # Add your Apify Token here for local runs

echo "Running Auto-Refill..."
python3 auto_refill.py

echo "Running Check Replies..."
python3 check_replies.py

echo "Running Outreach Script..."
python3 send_outreach.py

echo "Done."
