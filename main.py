from fastapi import FastAPI, Request, logger
from fastapi.responses import PlainTextResponse

from whatsapp.utils import verify_webhook

app = FastAPI()

logging = logger.logger


@app.get("/")
def health():
    logging.info("Test Logger", exc_info=1)
    return {"message": "Health check"}


@app.get("/webhook")
def verification(request: Request):
    response = verify_webhook(request)
    return PlainTextResponse(response)


@app.post("/webhook")
def notification():
    pass
