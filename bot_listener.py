import json
import logging
import logging.handlers
import os
import sys
import time
import threading
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

STORIES_DIR = BASE_DIR / "stories"

RATING_LABELS = {1: "😞 差", 2: "😐 一般", 3: "😊 好", 4: "🤩 超好"}

# ── Log rotation ──────────────────────────────────────────────────
_log_file = BASE_DIR / "bot_listener.log"
_handler = logging.handlers.RotatingFileHandler(
    _log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[_handler, logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

from novel_generator import GENRES
from utils import (
    load_genre_data, save_genre_data,
    send_telegram, send_toc_menu,
)


# ── 基礎工具 ──────────────────────────────────────────────────────

def answer_callback(callback_query_id, text=""):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    requests.post(
        f"https://api.telegram.org/bot{token}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": text, "show_alert": False},
        timeout=10,
    )


def register_commands():
    """向 Telegram 登記指令，令用戶打 / 時自動顯示選單。"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    commands = [
        {"command": "now",     "description": "即時生成1篇新故事"},
        {"command": "list",    "description": "瀏覽所有類別，tap 即生成"},
        {"command": "more",    "description": "從你的高分類別加推1篇"},
        {"command": "stats",   "description": "查看各類別評分統計"},
        {"command": "menu",    "description": "重讀今日故事目錄"},
        {"command": "history", "description": "瀏覽最近7日故事"},
        {"command": "help",    "description": "指令說明"},
    ]
    requests.post(
        f"https://api.telegram.org/bot{token}/setMyCommands",
        json={"commands": commands},
        timeout=10,
    )


# ── 故事讀取與發送 ────────────────────────────────────────────────

def get_today_stories():
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = STORIES_DIR / f"{today}.json"
    if filepath.exists():
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    return None


def get_stories_by_date(date_str: str):
    """讀取指定日期（YYYY-MM-DD）的故事，不存在返回 None。"""
    filepath = STORIES_DIR / f"{date_str}.json"
    if filepath.exists():
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    return None


def handle_history():
    """顯示最近 7 日有故事的日期選單。"""
    available = []
    for i in range(1, 8):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if (STORIES_DIR / f"{d}.json").exists():
            available.append(d)
    if not available:
        send_telegram("最近 7 日未有故事存檔。")
        return
    keyboard = [[{
        "text": d,
        "callback_data": f"hist_{d}"
    }] for d in available]
    send_telegram("📅 選擇日期重讀故事：", reply_markup={"inline_keyboard": keyboard})


def send_story(story_num, stories):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    s = stories[story_num - 1]
    header = (
        f"📖 [{story_num}/{len(stories)}]  {s['genre']}\n"
        f"👤 {s['character']['name']} · {s['character']['gender']} · {s['character']['occupation']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    full_text = header + s["content"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    max_len = 4000
    chunks = [full_text[i:i + max_len] for i in range(0, len(full_text), max_len)]
    for idx, chunk in enumerate(chunks):
        payload = {"chat_id": chat_id, "text": chunk}
        if idx == len(chunks) - 1:
            payload["reply_markup"] = {"inline_keyboard": [[
                {"text": "😞 差",   "callback_data": f"rate_{story_num}_1"},
                {"text": "😐 一般", "callback_data": f"rate_{story_num}_2"},
                {"text": "😊 好",   "callback_data": f"rate_{story_num}_3"},
                {"text": "🤩 超好", "callback_data": f"rate_{story_num}_4"},
            ]]}
        requests.post(url, json=payload, timeout=15)


# ── 評分與統計 ────────────────────────────────────────────────────

def record_rating(genre_name, score):
    data = load_genre_data()
    ratings = data.setdefault("ratings", {})
    ratings.setdefault(genre_name, []).append(score)
    ratings[genre_name] = ratings[genre_name][-10:]
    save_genre_data(data)
    avg = sum(ratings[genre_name]) / len(ratings[genre_name])
    return avg, len(ratings[genre_name])


def record_winner(genre_name, opening, villain):
    data = load_genre_data()
    winners = data.setdefault("winners", {})
    entries = winners.setdefault(genre_name, [])
    entries.append({"opening": opening, "villain": villain})
    winners[genre_name] = entries[-5:]
    save_genre_data(data)


def handle_rating(story_num, score, stories):
    if not stories or story_num < 1 or story_num > len(stories):
        return "搵唔到故事", None
    story = stories[story_num - 1]
    genre_name = story["genre"]
    avg, count = record_rating(genre_name, score)
    reply = f"《{genre_name}》已記錄：{RATING_LABELS[score]}"
    if count >= 3:
        if avg < 2:
            reply += "\n⚠️ 評分持續偏低，此類別出現頻率已降低"
        elif avg >= 3.8:
            reply += "\n⭐ 高分類別，出現頻率已提升"
    if score == 4:
        opening = story.get("opening", "")
        villain = story.get("villain", "")
        if opening or villain:
            record_winner(genre_name, opening, villain)
        return reply, genre_name
    return reply, None


def handle_bonus_rating(score, genre_name):
    avg, count = record_rating(genre_name, score)
    reply = f"《{genre_name}》已記錄：{RATING_LABELS[score]}"
    if score == 4:
        return reply, genre_name
    return reply, None


def handle_stats():
    data = load_genre_data()
    ratings = data.get("ratings", {})
    if not ratings:
        send_telegram("未有評分記錄，生成幾篇故事後再試。")
        return

    scored = []
    for name, scores in ratings.items():
        if scores:
            scored.append((name, sum(scores) / len(scores), len(scores)))
    scored.sort(key=lambda x: x[1], reverse=True)

    lines = ["📊 各類別評分統計\n"]
    for name, avg, count in scored:
        bar = "⭐" * round(avg)
        lines.append(f"{bar}  {name}（{avg:.1f}分 / {count}次）")

    send_telegram("\n".join(lines))


# ── /list 類別選單 ────────────────────────────────────────────────

def handle_list():
    """顯示所有類別，每個都係可以 tap 直接生成的按鈕。"""
    keyboard = []
    row = []
    for i, g in enumerate(GENRES):
        row.append({"text": g["name"], "callback_data": f"pick_{g['name']}"})
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    send_telegram("📚 選擇類別，tap 即生成：", reply_markup={"inline_keyboard": keyboard})


# ── Callback 處理 ─────────────────────────────────────────────────

def handle_callback(cb):
    cb_data = cb.get("data", "")

    if cb_data.startswith("story_"):
        story_num = int(cb_data.split("_")[1])
        stories = get_today_stories()
        if stories and 1 <= story_num <= len(stories):
            answer_callback(cb["id"], "發送中...")
            send_story(story_num, stories)
        else:
            answer_callback(cb["id"], "今日故事未生成")

    elif cb_data.startswith("rate_"):
        parts = cb_data.split("_")
        story_num = int(parts[1])
        score = int(parts[2])
        stories = get_today_stories()
        reply, hot_genre = handle_rating(story_num, score, stories)
        answer_callback(cb["id"], reply)
        if hot_genre:
            send_telegram(
                f"🔥 高分！幫你加推一篇《{hot_genre}》？",
                reply_markup={"inline_keyboard": [[
                    {"text": f"➕ 加推《{hot_genre}》", "callback_data": f"more_{hot_genre}"},
                    {"text": "不用了", "callback_data": "more_skip"},
                ]]}
            )

    elif cb_data.startswith("ratex_"):
        parts = cb_data.split("_", 2)
        score = int(parts[1])
        genre_name = parts[2]
        reply, hot_genre = handle_bonus_rating(score, genre_name)
        answer_callback(cb["id"], reply)
        if hot_genre:
            send_telegram(
                f"🔥 高分！幫你再推一篇《{hot_genre}》？",
                reply_markup={"inline_keyboard": [[
                    {"text": f"➕ 加推《{hot_genre}》", "callback_data": f"more_{hot_genre}"},
                    {"text": "不用了", "callback_data": "more_skip"},
                ]]}
            )

    elif cb_data.startswith("hist_"):
        date_str = cb_data[5:]
        stories = get_stories_by_date(date_str)
        if stories:
            answer_callback(cb["id"], f"載入 {date_str} 故事...")
            send_toc_menu(stories)
        else:
            answer_callback(cb["id"], "找不到該日故事")

    elif cb_data.startswith("pick_"):
        genre_name = cb_data[5:]
        answer_callback(cb["id"], f"生成《{genre_name}》中...")
        threading.Thread(target=_run_generate_one, args=(genre_name,), daemon=True).start()

    elif cb_data.startswith("more_"):
        genre_name = cb_data[5:]
        if genre_name == "skip":
            answer_callback(cb["id"], "好，下次見！")
            return
        answer_callback(cb["id"], "生成中，稍等...")
        threading.Thread(target=_run_generate_one, args=(genre_name,), daemon=True).start()


# ── 生成執行緒 ────────────────────────────────────────────────────

def _run_generate_one(genre_name=None):
    try:
        from novel_generator import generate_and_send_one
        generate_and_send_one(genre_name)
    except Exception as e:
        send_telegram(f"⚠️ 生成失敗：{e}")


# ── 文字指令處理 ──────────────────────────────────────────────────

def cmd(text, command):
    return text == command or text.startswith(command + "@")


def handle_message(text):
    stories = get_today_stories()

    if cmd(text, "/help") or cmd(text, "/start"):
        send_telegram(
            "📖 小說機器人指令\n\n"
            "/now — 即時生成1篇新故事\n"
            "/list — 瀏覽所有類別，tap 即生成\n"
            "/more — 從高分類別加推1篇\n"
            "/stats — 查看各類別評分統計\n"
            "/menu — 重讀今日故事目錄\n"
            "/history — 瀏覽最近7日故事\n\n"
            "💡 打 / 可快速呼出所有指令"
        )
        return

    if cmd(text, "/now"):
        send_telegram("✨ 即時生成1篇新故事，請稍候...")
        threading.Thread(target=_run_generate_one, args=(None,), daemon=True).start()
        return

    if cmd(text, "/list"):
        handle_list()
        return

    if cmd(text, "/more"):
        send_telegram("✨ 從你的高分類別加推1篇，生成中...")
        threading.Thread(target=_run_generate_one, args=(None,), daemon=True).start()
        return

    if cmd(text, "/stats"):
        handle_stats()
        return

    if cmd(text, "/menu"):
        if stories:
            send_toc_menu(stories)
        else:
            send_telegram("未有故事，用 /now 即時生成或 /list 選類別。")
        return

    if cmd(text, "/history"):
        handle_history()
        return

    if cmd(text, "/pick"):
        genre_name = text.split(maxsplit=1)[1].strip() if len(text.split()) > 1 else ""
        if genre_name:
            send_telegram(f"✨ 生成《{genre_name}》中...")
            threading.Thread(target=_run_generate_one, args=(genre_name,), daemon=True).start()
        else:
            handle_list()
        return


# ── 主循環 ────────────────────────────────────────────────────────

def poll():
    register_commands()
    log.info(f"Bot listener 啟動 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/getUpdates"
    offset = None

    while True:
        try:
            params = {
                "timeout": 30,
                "allowed_updates": ["message", "callback_query"],
                "offset": offset,
            }
            resp = requests.get(url, params=params, timeout=35)
            data = resp.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                if "callback_query" in update:
                    handle_callback(update["callback_query"])
                elif "message" in update:
                    text = update["message"].get("text", "").strip()
                    if text:
                        log.info(f"收到指令: {text!r}")
                        handle_message(text)

        except Exception as e:
            log.error(f"Poll error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    poll()
