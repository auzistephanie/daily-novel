import os
import threading
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
log = logging.getLogger(__name__)

from bot_listener import handle_message, handle_callback, register_commands

ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("TG_WEBHOOK_SECRET")


def _authorized(data):
    """只接受本人（TELEGRAM_CHAT_ID）發出的 update。"""
    msg = data.get("message") or data.get("callback_query", {}).get("message") or {}
    chat_id = str(msg.get("chat", {}).get("id", ""))
    return bool(ALLOWED_CHAT_ID) and chat_id == str(ALLOWED_CHAT_ID)


@app.route("/webhook", methods=["POST"])
def webhook():
    # 1) 驗 Telegram secret token（setWebhook 時註冊，非 Telegram 來源直接擋）
    if not WEBHOOK_SECRET or request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return jsonify({"ok": False}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False}), 400

    # 2) 驗寄件者為本人，非本人靜默丟棄（回 200 避免 Telegram 重投遞）
    if not _authorized(data):
        log.warning("拒絕非授權寄件者")
        return jsonify({"ok": True})

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


if __name__ == "__main__":
    register_commands()
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
