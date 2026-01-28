"""
WhatsApp Cloud API Webhook — Connects the bookkeeper to real WhatsApp.

Setup (one-time):
  1. Go to https://developers.facebook.com → Create App → Business type
  2. Add "WhatsApp" product → Go to API Setup
  3. Note your: Phone Number ID, Access Token, Verify Token
  4. Set environment variables (see below)
  5. Run this server and expose it with ngrok
  6. Register the webhook URL in Meta dashboard

Environment variables:
  WHATSAPP_PHONE_ID    — Your WhatsApp Business phone number ID
  WHATSAPP_TOKEN       — Permanent or temporary access token
  WHATSAPP_VERIFY      — Any string you choose (used for webhook verification)
  OPENAI_API_KEY       — (Optional) For LLM-powered extraction/summaries

Usage:
  pip install flask requests
  export WHATSAPP_PHONE_ID="123456"
  export WHATSAPP_TOKEN="EAAx..."
  export WHATSAPP_VERIFY="my-secret-token"
  python -m whatsapp_bookkeeper.webhook

  # In another terminal, expose with ngrok:
  ngrok http 5000

  # Then paste the ngrok HTTPS URL into Meta's webhook config:
  # URL: https://xxxx.ngrok.io/webhook
  # Verify token: my-secret-token
"""

import os
import json
import tempfile
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load .env file from the project root (two levels up from this file)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .whatsapp_sim import process_receipt, process_text_message

app = Flask(__name__)

# ── Configuration ─────────────────────────────────────────────────────────
PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
ACCESS_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY", "bookkeeper-verify")

API_URL = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
MEDIA_URL = "https://graph.facebook.com/v21.0"
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


# ── Webhook verification (GET) ───────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def verify():
    """Meta sends a GET request to verify the webhook URL."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return challenge, 200

    return "Forbidden", 403


# ── Incoming messages (POST) ──────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def receive_message():
    """Handle incoming WhatsApp messages."""
    body = request.get_json()

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Skip status updates (delivered, read, etc.)
        if "messages" not in value:
            return jsonify({"status": "ok"}), 200

        message = value["messages"][0]
        sender = message["from"]  # phone number
        msg_type = message["type"]

        print(f"📩 Message from {sender} (type: {msg_type})")

        if msg_type == "image":
            # Download the image, process as receipt
            media_id = message["image"]["id"]
            caption = message["image"].get("caption", "")
            reply = _handle_image(media_id, caption)

        elif msg_type == "text":
            text = message["text"]["body"]
            reply = process_text_message(text)

        else:
            reply = (
                "📷 Envie uma foto de recibo ou uma mensagem de texto.\n"
                "Digite \"ajuda\" para ver os comandos."
            )

        _send_reply(sender, reply)

    except (KeyError, IndexError) as e:
        print(f"⚠️ Could not parse message: {e}")

    return jsonify({"status": "ok"}), 200


# ── Image handling ────────────────────────────────────────────────────────

def _handle_image(media_id: str, caption: str = "") -> str:
    """Download a WhatsApp image and process it as a receipt."""
    # Step 1: Get the media URL
    media_resp = requests.get(
        f"{MEDIA_URL}/{media_id}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    media_resp.raise_for_status()
    media_url = media_resp.json()["url"]

    # Step 2: Download the image
    img_resp = requests.get(
        media_url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    img_resp.raise_for_status()

    # Step 3: Save to temp file and process
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(img_resp.content)
        tmp_path = f.name

    try:
        return process_receipt(tmp_path, caption)
    finally:
        os.unlink(tmp_path)


# ── Send reply ────────────────────────────────────────────────────────────

def _send_reply(to: str, text: str) -> None:
    """Send a text message back via WhatsApp Cloud API."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload)

    if resp.ok:
        print(f"✅ Reply sent to {to}")
    else:
        print(f"❌ Failed to send: {resp.status_code} {resp.text}")


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not PHONE_ID or not ACCESS_TOKEN:
        print("=" * 60)
        print("  ⚠️  Missing environment variables!")
        print()
        print("  Set these before running:")
        print("    export WHATSAPP_PHONE_ID='your-phone-number-id'")
        print("    export WHATSAPP_TOKEN='your-access-token'")
        print("    export WHATSAPP_VERIFY='your-verify-token'")
        print()
        print("  Get these from:")
        print("    https://developers.facebook.com/apps → WhatsApp → API Setup")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  📱 WhatsApp Bookkeeper — Webhook Server")
        print(f"  Phone ID: {PHONE_ID[:8]}...")
        print()
        print("  Expose this server with ngrok:")
        print("    ngrok http 5000")
        print()
        print("  Then register the webhook URL in Meta dashboard:")
        print("    URL: https://xxxx.ngrok.io/webhook")
        print(f"    Verify Token: {VERIFY_TOKEN}")
        print("=" * 60)

    app.run(port=5000, debug=True)
