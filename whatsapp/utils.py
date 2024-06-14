import hashlib
import hmac
import json
import os
from urllib.parse import parse_qs
import requests

from dotenv import load_dotenv
from fastapi import logger

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

logging = logger.logger


def verify_webhook(request):
    query_params = parse_qs(str(request.query_params))
    mode = query_params.get("hub.mode", None)
    token = query_params.get("hub.verify_token", None)
    challenge = query_params.get("hub.challenge", None)

    if mode and token:
        if mode[0] == "subscribe" and token[0] == VERIFY_TOKEN:
            return challenge[0]
        else:
            return "Invalid verification token"


async def handle_webhook(request):
    if request.method == "POST":
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature", "")

        if not verify_signature(body, signature):
            return "Invalid signature", 403

        data = json.loads(body)

        entry = data["entry"][0]
        messaging_events = [
            changes.get("value")
            for changes in entry.get("changes", [])
            if changes.get("value")
        ]

        if messaging_events[0].get("statuses"):
            return "OK"

        # for event in messaging_events:
        recipient_id = messaging_events[0]["metadata"]["display_phone_number"]
        phone_number_id = messaging_events[0]["metadata"]["phone_number_id"]
        message = messaging_events[0]["messages"][0]
        sender_id = message["from"]
        logging.info(f"{sender_id} {phone_number_id} {message}")

    return "OK"


def verify_signature(request_body, signature):
    if signature.startswith("sha1="):
        sha1 = hmac.new(
            APP_SECRET.encode("utf-8"), request_body, hashlib.sha1
        ).hexdigest()
        return sha1 == signature[5:]
    else:
        return False


def handle_message(sender_id, recipient_id, message):
    message_text = None
    if message.get("text"):
        message_text = message["text"]["body"]

    response = message_text
    send_message(recipient_id, sender_id, response)


def send_message(phone_number_id, recipient_id, message):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "text",
        "text": {
            "preview_url": True,
            "body": message,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PAGE_ACCESS_TOKEN}",
    }

    response = requests.post(
        f"https://graph.facebook.com/v20.0/{phone_number_id}/messages",
        json=payload,
        headers=headers,
    )
    if response.status_code != 200:
        return "Failed to send message:", response.status_code
    else:
        return "Message sent to", recipient_id
