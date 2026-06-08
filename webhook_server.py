import os
import threading
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Flask(__name__)
log = logging.getLogger(__name__)

from bot_listener import handle_message, handle_callback, register_commands


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False}), 400

    try:
        if "callback_query" in data:
            threading.Thread(
                target=handle_callback,
                args=(data["callback_query"],),
                daemon=True,
            ).start()
        elif "message" in data:
            text = data["message"].get("text", "").strip()
            if text:
                log.info(f"收到指令: {text!r}")
                threading.Thread(
                    target=handle_message,
                    args=(text,),
                    daemon=True,
                ).start()
    except Exception as e:
        log.error(f"Webhook error: {e}")

    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"


@app.route("/debug", methods=["GET"])
def debug():
    import requests as req
    token = os.getenv("TELEGRAM_BOT_TOKEN", "NOT SET")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "NOT SET")
    r = req.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
    return jsonify({
        "token_last10": token[-10:] if len(token) > 10 else token,
        "chat_id": chat_id,
        "getMe": r.json()
    })


if __name__ == "__main__":
    register_commands()
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
