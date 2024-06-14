from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from whatsapp.utils import verify_webhook, handle_webhook

app = FastAPI()


@app.get("/")
def health():
    return {"message": "Health check"}


@app.get("/webhook")
def verification(request: Request):
    response = verify_webhook(request)
    return PlainTextResponse(response)


@app.post("/webhook")
async def notification(request: Request):
    response = await handle_webhook(request)
    return PlainTextResponse(str(response))
