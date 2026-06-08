"""共用工具函數：genre data I/O、Telegram 發送、目錄選單。"""

import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GENRE_DATA_FILE = BASE_DIR / "genre_data.json"


# ── Genre Data ────────────────────────────────────────────────────

def load_genre_data() -> dict:
    if GENRE_DATA_FILE.exists():
        with open(GENRE_DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"recent_genres": [], "ratings": {}}


def save_genre_data(data: dict) -> None:
    with open(GENRE_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Telegram ──────────────────────────────────────────────────────

def _split_text(text: str, max_len: int = 4000) -> list:
    """在段落邊界（\\n\\n）分割文字，避免切斷句子中間。"""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while len(text) > max_len:
        # 從 max_len 位置往前找最近的段落邊界
        split_pos = text.rfind("\n\n", 0, max_len)
        if split_pos == -1:
            # 找不到段落邊界，退而求其次找換行
            split_pos = text.rfind("\n", 0, max_len)
        if split_pos == -1:
            # 完全找不到，硬切
            split_pos = max_len
        chunks.append(text[:split_pos].rstrip())
        text = text[split_pos:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def send_telegram(text: str, reply_markup=None, max_retries: int = 3) -> None:
    """發送訊息，在段落邊界分割超長文字，失敗最多重試 max_retries 次。"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chunks = _split_text(text)
    for idx, chunk in enumerate(chunks):
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk}
        if reply_markup and idx == len(chunks) - 1:
            payload["reply_markup"] = reply_markup
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=15)
                if resp.ok:
                    break
                print(f"Telegram 發送失敗（第 {attempt} 次）: {resp.text}")
            except requests.RequestException as e:
                print(f"Telegram 請求異常（第 {attempt} 次）: {e}")


def send_toc_menu(stories_data: list) -> None:
    """發送今日故事目錄（可點擊的 inline keyboard）。"""
    keyboard = []
    for i, s in enumerate(stories_data, 1):
        keyboard.append([{
            "text": f"{i}.  {s['genre']}  ·  {s['character']['name']}",
            "callback_data": f"story_{i}"
        }])
    send_telegram(
        "📋 今日故事目錄\n點擊任何一篇即可重讀：",
        reply_markup={"inline_keyboard": keyboard}
    )
