import hashlib
import hmac
import json
import os
from urllib.parse import parse_qs
import requests

from dotenv import load_dotenv
from fastapi import Request
import logging
from agent import abot

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_webhook(request: Request) -> str:
    query_params = parse_qs(str(request.query_params))
    mode = query_params.get("hub.mode", None)
    token = query_params.get("hub.verify_token", None)
    challenge = query_params.get("hub.challenge", None)

    if mode and token:
        if mode[0] == "subscribe" and token[0] == VERIFY_TOKEN:
            return challenge[0]
        else:
            return "Invalid verification token"
    return "Missing mode or token"


async def handle_webhook(request: Request) -> str:
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

        # Process the first messaging event
        recipient_id = messaging_events[0]["metadata"]["display_phone_number"]
        phone_number_id = messaging_events[0]["metadata"]["phone_number_id"]
        message = messaging_events[0]["messages"][0]
        sender_id = message["from"]
        handle_message(sender_id, phone_number_id, message)

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

    messages = [HumanMessage(content=message_text)]
    result = abot.graph.invoke({"messages": messages})
    send_message(recipient_id, sender_id, result)


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
        logging.error(response.text)
        logging.error(f"Failed to send message: {response.status_code}")
        return f"Failed to send message: {response.status_code}"
    else:
        logging.info(f"Message sent to {recipient_id}")
        return f"Message sent to {recipient_id}"
