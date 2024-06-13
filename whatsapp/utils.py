import json
import os
from urllib.parse import parse_qs

from dotenv import load_dotenv
from fastapi import logger

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")

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
