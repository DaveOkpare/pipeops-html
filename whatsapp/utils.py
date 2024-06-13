import os
from urllib.parse import parse_qs

from dotenv import load_dotenv

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


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
