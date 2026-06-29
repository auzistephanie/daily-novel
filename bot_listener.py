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
FAVS_FILE   = BASE_DIR / "favourites.json"

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
from lit_generator import LIT_GENRES
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


def _typing_loop(stop_event):
    """每 4 秒發一次 typing action，令用家知道 bot 仍在工作。"""
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendChatAction"
    while not stop_event.is_set():
        try:
            requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=5)
        except Exception:
            pass
        stop_event.wait(4)


# ── 收藏功能 ──────────────────────────────────────────────────────

def load_favourites() -> list:
    if FAVS_FILE.exists():
        with open(FAVS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_favourites(favs: list) -> None:
    FAVS_FILE.write_text(json.dumps(favs, ensure_ascii=False, indent=2), encoding="utf-8")


def add_favourite_by_num(story_num: int) -> bool:
    """從今日故事（by index）加入收藏，返回是否成功。"""
    stories = get_today_stories()
    if not stories or story_num < 1 or story_num > len(stories):
        return False
    s = stories[story_num - 1]
    today = datetime.now().strftime("%Y-%m-%d")
    return _append_fav(today, s)


def add_favourite_by_genre(genre_name: str) -> bool:
    """從今日故事（by genre name）加入收藏，返回是否成功。"""
    stories = get_today_stories()
    if not stories:
        return False
    # 取最近一篇（list 末尾）
    matches = [s for s in stories if s["genre"] == genre_name]
    if not matches:
        return False
    s = matches[-1]
    today = datetime.now().strftime("%Y-%m-%d")
    return _append_fav(today, s)


def _append_fav(date: str, story: dict) -> bool:
    favs = load_favourites()
    # 避免重複
    for f in favs:
        if f["date"] == date and f["genre"] == story["genre"]:
            return False
    favs.append({
        "date":           date,
        "genre":          story["genre"],
        "type":           story.get("type", "novel"),
        "mood":           story.get("mood", ""),
        "character_name": story["character"]["name"],
        "saved_at":       datetime.now().isoformat()[:16],
    })
    _save_favourites(favs[-20:])  # 最多保留 20 篇
    return True


def handle_fav():
    """顯示收藏故事列表。"""
    favs = load_favourites()
    if not favs:
        send_telegram("未有收藏故事。讀完故事後，評分時 tap ⭐ 收藏。")
        return
    keyboard = []
    for i, f in enumerate(reversed(favs)):  # 最新在上
        icon = "📚" if f["type"] == "lit" else "📖"
        keyboard.append([{
            "text": f"{icon} {f['genre']}  ·  {f['character_name']}  ({f['date']})",
            "callback_data": f"favread_{len(favs)-1-i}",
        }])
    send_telegram("⭐ 收藏故事（最新在上）：", reply_markup={"inline_keyboard": keyboard})


def send_fav_story(fav_idx: int):
    """重讀收藏故事。"""
    favs = load_favourites()
    if fav_idx < 0 or fav_idx >= len(favs):
        send_telegram("找不到該收藏故事。")
        return
    f = favs[fav_idx]
    filepath = STORIES_DIR / f"{f['date']}.json"
    if not filepath.exists():
        send_telegram(f"原始檔案已不存在（{f['date']}）。")
        return
    with open(filepath, encoding="utf-8") as fp:
        stories = json.load(fp)
    story = next((s for s in stories if s["genre"] == f["genre"]), None)
    if not story:
        send_telegram("找不到該故事內容。")
        return
    char = story["character"]
    if story.get("type") == "lit":
        header = (
            f"📚 [⭐收藏]  {story['genre']}\n"
            f"👤 {char['name']} · {char['gender']} · {char['occupation']}\n"
            f"🎭 {story.get('mood', '')}  ·  {story.get('style', '')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    else:
        ch_tag = "🔥 男頻" if story.get("channel", "M") == "M" else "💕 女頻"
        header = (
            f"📖 [⭐收藏]  {story['genre']}\n"
            f"👤 {char['name']} · {char['gender']} · {char['occupation']}  ｜  {ch_tag}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    send_telegram(header + story["content"])


def register_commands():
    """向 Telegram 登記指令，令用戶打 / 時自動顯示選單。"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    commands = [
        {"command": "now",     "description": "即時生成1篇爽文"},
        {"command": "list",    "description": "選頻道 → 選類別 → 生成"},
        {"command": "more",    "description": "從高分類別加推1篇"},
        {"command": "lit",     "description": "即時生成1篇情感文學故事"},
        {"command": "litlist", "description": "選情緒基調 → 選類別 → 生成"},
        {"command": "today",   "description": "今日故事目錄"},
        {"command": "fav",     "description": "收藏故事"},
        {"command": "stats",   "description": "各類別評分統計"},
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
    s = stories[story_num - 1]
    story_type = s.get("type", "novel")
    char = s["character"]

    if story_type == "lit":
        header = (
            f"📚 [{story_num}/{len(stories)}]  {s['genre']}\n"
            f"👤 {char['name']} · {char['gender']} · {char['occupation']}\n"
            f"🎭 {s.get('mood', '')}  ·  {s.get('style', '')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    else:
        ch = s.get("channel", "M")
        ch_tag = "🔥 男頻" if ch == "M" else "💕 女頻"
        header = (
            f"📖 [{story_num}/{len(stories)}]  {s['genre']}\n"
            f"👤 {char['name']} · {char['gender']} · {char['occupation']}  ｜  {ch_tag}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

    rating_keyboard = {"inline_keyboard": [[
        {"text": "😞 差",   "callback_data": f"rate_{story_num}_1"},
        {"text": "😐 一般", "callback_data": f"rate_{story_num}_2"},
        {"text": "😊 好",   "callback_data": f"rate_{story_num}_3"},
        {"text": "🤩 超好", "callback_data": f"rate_{story_num}_4"},
    ]]}
    send_telegram(header + s["content"], reply_markup=rating_keyboard)


# ── 評分與統計 ────────────────────────────────────────────────────

def record_rating(genre_name, score):
    data = load_genre_data()
    ratings = data.setdefault("ratings", {})
    ratings.setdefault(genre_name, []).append(score)
    ratings[genre_name] = ratings[genre_name][-10:]
    save_genre_data(data)
    avg = sum(ratings[genre_name]) / len(ratings[genre_name])
    return avg, len(ratings[genre_name])


def record_winner(genre_name, dna: dict):
    """存入高分故事的完整 DNA，保留最近 5 個 winner。"""
    data = load_genre_data()
    winners = data.setdefault("winners", {})
    entries = winners.setdefault(genre_name, [])
    entries.append(dna)
    winners[genre_name] = entries[-5:]
    save_genre_data(data)


def record_cooldown(dna: dict):
    """把低分故事的 DNA 元素推到 recent_dna 前端，強迫冷卻更長時間。"""
    from utils import load_recent_dna, save_recent_dna
    try:
        recent = load_recent_dna()
        COOLDOWN_WINDOW = 12  # 比正常 window(5) 大，強制更長冷卻
        for key in ["setting", "irony", "trump_card", "villain_flaw",
                    "emotional_core", "memorable", "structure"]:
            val = dna.get(key, "")
            if not val:
                continue
            lst = recent.get(key, [])
            if val in lst:
                lst.remove(val)
            lst = [val] + lst          # 推到最前，佔住冷卻位最久
            recent[key] = lst[:COOLDOWN_WINDOW]
        save_recent_dna(recent)
    except Exception as e:
        log.error(f"record_cooldown error: {e}")


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

    dna = story.get("dna", {})
    if score <= 2 and dna:
        record_cooldown(dna)
    if score == 4:
        if dna:
            record_winner(genre_name, dna)
        elif story.get("opening") or story.get("villain"):
            # 舊格式兼容
            record_winner(genre_name, {
                "opening": story.get("opening", ""),
                "villain": story.get("villain", ""),
            })
        return reply, genre_name
    return reply, None


def handle_bonus_rating(score, genre_name):
    avg, count = record_rating(genre_name, score)
    reply = f"《{genre_name}》已記錄：{RATING_LABELS[score]}"

    # 讀取剛才生成嗰篇嘅 DNA
    try:
        from utils import load_story_dna
        dna = load_story_dna(genre_name)
    except Exception:
        dna = {}

    if score <= 2 and dna:
        record_cooldown(dna)
    if score == 4:
        if dna:
            record_winner(genre_name, dna)
        return reply, genre_name
    return reply, None


def handle_stats():
    data = load_genre_data()
    ratings = data.get("ratings", {})
    if not ratings:
        send_telegram("未有評分記錄，生成幾篇故事後再試。")
        return

    # ── Genre 評分排行 ────────────────────────────────────────────
    scored = []
    for name, scores in ratings.items():
        if scores:
            scored.append((name, sum(scores) / len(scores), len(scores)))
    scored.sort(key=lambda x: x[1], reverse=True)

    lines = ["📊 各類別評分統計\n"]
    for name, avg, count in scored:
        bar = "⭐" * round(avg)
        lines.append(f"{bar}  {name}（{avg:.1f}分 / {count}次）")

    # ── DNA 元素洞察（高分故事用咗咩）────────────────────────────
    winners = data.get("winners", {})
    dna_tallies: dict[str, dict[str, int]] = {}
    for genre_winners in winners.values():
        for w in genre_winners:
            for key in ["irony", "structure", "emotional_core", "trump_card"]:
                val = w.get(key, "")
                if val:
                    short = val[:24] + "…" if len(val) > 24 else val
                    dna_tallies.setdefault(key, {})
                    dna_tallies[key][short] = dna_tallies[key].get(short, 0) + 1

    if dna_tallies:
        lines.append("\n\n🧬 你最鍾意的故事元素（高分故事統計）\n")
        labels = {
            "irony":          "諷刺結構",
            "structure":      "敘事結構",
            "emotional_core": "情感核心",
            "trump_card":     "主角王牌",
        }
        for key, label in labels.items():
            if key not in dna_tallies:
                continue
            top = sorted(dna_tallies[key].items(), key=lambda x: x[1], reverse=True)[:2]
            if top:
                lines.append(f"【{label}】")
                for text, cnt in top:
                    lines.append(f"  • {text}（{cnt}次）")

    send_telegram("\n".join(lines))


# ── /list 及 /litlist 類別選單 ───────────────────────────────────

def handle_list():
    """顯示爽文頻道選擇（男頻/女頻），tap 後再選具體類別。"""
    m_count = sum(1 for g in GENRES if g.get("channel") == "M")
    f_count = sum(1 for g in GENRES if g.get("channel") == "F")
    keyboard = [[
        {"text": f"🔥 男頻爽文（{m_count}類）", "callback_data": "listch_M"},
        {"text": f"💕 女頻言情（{f_count}類）", "callback_data": "listch_F"},
    ]]
    send_telegram("📚 選擇頻道：", reply_markup={"inline_keyboard": keyboard})


def handle_list_channel(channel: str):
    """顯示指定頻道的爽文類別列表。"""
    label = "🔥 男頻爽文" if channel == "M" else "💕 女頻言情"
    genres = [g for g in GENRES if g.get("channel") == channel]
    keyboard = []
    row = []
    for g in genres:
        row.append({"text": g["name"], "callback_data": f"pick_{g['name']}"})
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    send_telegram(f"{label} — tap 即生成：", reply_markup={"inline_keyboard": keyboard})


_LIT_MOOD_EMOJI = {
    "溫暖": "🌞", "敬畏": "🌌", "唏噓": "😔", "解氣": "🔥",
    "治癒": "🌿", "心酸": "💧", "餘韻": "🌙", "荒謬": "🎭",
}


def handle_litlist():
    """顯示情感文學的情緒分類，tap 後再選具體故事類型。"""
    from collections import defaultdict
    by_mood = defaultdict(int)
    for g in LIT_GENRES:
        by_mood[g["mood"]] += 1
    keyboard = []
    row = []
    for mood, count in sorted(by_mood.items(), key=lambda x: -x[1]):
        emoji = _LIT_MOOD_EMOJI.get(mood, "📖")
        row.append({"text": f"{emoji} {mood}（{count}）", "callback_data": f"litmd_{mood}"})
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    send_telegram("📖 選擇情緒基調：", reply_markup={"inline_keyboard": keyboard})


def handle_litlist_mood(mood: str):
    """顯示指定情緒基調的情感文學類別。"""
    emoji = _LIT_MOOD_EMOJI.get(mood, "📖")
    genres = [g for g in LIT_GENRES if g["mood"] == mood]
    keyboard = []
    row = []
    for g in genres:
        row.append({"text": g["name"], "callback_data": f"picklit_{g['name']}"})
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    send_telegram(f"{emoji} {mood} — tap 即生成：", reply_markup={"inline_keyboard": keyboard})


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
        _again_row = [
            {"text": "🔁 再來爽文",   "callback_data": "again_novel"},
            {"text": "🔁 再來情感文學", "callback_data": "again_lit"},
        ]
        if hot_genre:
            send_telegram(
                f"🤩 《{hot_genre}》超好！",
                reply_markup={"inline_keyboard": [
                    [{"text": f"➕ 加推《{hot_genre}》", "callback_data": f"more_{hot_genre}"},
                     {"text": "⭐ 收藏",                "callback_data": f"fav_{story_num}"}],
                    _again_row,
                ]}
            )
        else:
            genre_name = stories[story_num - 1]["genre"] if stories else "?"
            send_telegram(
                f"{RATING_LABELS[score]} 《{genre_name}》已記錄",
                reply_markup={"inline_keyboard": [_again_row]}
            )

    elif cb_data.startswith("ratex_"):
        parts = cb_data.split("_", 2)
        score = int(parts[1])
        genre_name = parts[2]
        reply, hot_genre = handle_bonus_rating(score, genre_name)
        answer_callback(cb["id"], reply)
        _again_row = [
            {"text": "🔁 再來爽文",   "callback_data": "again_novel"},
            {"text": "🔁 再來情感文學", "callback_data": "again_lit"},
        ]
        if hot_genre:
            send_telegram(
                f"🤩 《{hot_genre}》超好！",
                reply_markup={"inline_keyboard": [
                    [{"text": f"➕ 加推《{hot_genre}》", "callback_data": f"more_{hot_genre}"},
                     {"text": "⭐ 收藏",                "callback_data": f"favx_{genre_name}"}],
                    _again_row,
                ]}
            )
        else:
            send_telegram(
                f"{RATING_LABELS[score]} 《{genre_name}》已記錄",
                reply_markup={"inline_keyboard": [_again_row]}
            )

    elif cb_data.startswith("hist_"):
        date_str = cb_data[5:]
        stories = get_stories_by_date(date_str)
        if stories:
            answer_callback(cb["id"], f"載入 {date_str} 故事...")
            send_toc_menu(stories)
        else:
            answer_callback(cb["id"], "找不到該日故事")

    elif cb_data.startswith("listch_"):
        channel = cb_data[7:]
        answer_callback(cb["id"], "載入類別...")
        handle_list_channel(channel)

    elif cb_data.startswith("litmd_"):
        mood = cb_data[6:]
        answer_callback(cb["id"], f"載入{mood}類別...")
        handle_litlist_mood(mood)

    elif cb_data.startswith("pick_"):
        genre_name = cb_data[5:]
        answer_callback(cb["id"], f"生成《{genre_name}》中...")
        threading.Thread(target=_run_generate_one, args=(genre_name, "[指定]"), daemon=True).start()

    elif cb_data.startswith("picklit_"):
        genre_name = cb_data[8:]
        answer_callback(cb["id"], f"生成《{genre_name}》中...")
        threading.Thread(target=_run_generate_lit, args=(genre_name,), daemon=True).start()

    elif cb_data == "again_novel":
        answer_callback(cb["id"], "再來一篇...")
        threading.Thread(target=_run_generate_one, args=(None, ""), daemon=True).start()

    elif cb_data == "again_lit":
        answer_callback(cb["id"], "再來情感文學...")
        threading.Thread(target=_run_generate_lit, args=(None,), daemon=True).start()

    elif cb_data.startswith("fav_"):
        story_num = int(cb_data[4:])
        ok = add_favourite_by_num(story_num)
        answer_callback(cb["id"], "⭐ 已收藏！" if ok else "已收藏過了")

    elif cb_data.startswith("favx_"):
        genre_name = cb_data[5:]
        ok = add_favourite_by_genre(genre_name)
        answer_callback(cb["id"], "⭐ 已收藏！" if ok else "已收藏過了")

    elif cb_data.startswith("favread_"):
        fav_idx = int(cb_data[8:])
        answer_callback(cb["id"], "載入收藏故事...")
        send_fav_story(fav_idx)

    elif cb_data.startswith("more_"):
        genre_name = cb_data[5:]
        if genre_name == "skip":
            answer_callback(cb["id"], "好，下次見！")
            return
        answer_callback(cb["id"], "加推生成中...")
        threading.Thread(target=_run_generate_one, args=(genre_name, "[加推]"), daemon=True).start()


# ── 生成執行緒 ────────────────────────────────────────────────────

def _run_generate_one(genre_name=None, label=""):
    stop = threading.Event()
    threading.Thread(target=_typing_loop, args=(stop,), daemon=True).start()
    try:
        from novel_generator import generate_and_send_one
        generate_and_send_one(genre_name, label=label)
    except Exception as e:
        import traceback
        print(f"[_run_generate_one] 錯誤：{traceback.format_exc()}")
        send_telegram("⚠️ 故事生成失敗，請稍後再試（/now 重新生成）")
    finally:
        stop.set()


def _run_generate_lit(genre_name=None):
    stop = threading.Event()
    threading.Thread(target=_typing_loop, args=(stop,), daemon=True).start()
    try:
        from lit_generator import generate_and_send_lit
        generate_and_send_lit(genre_name)
    except Exception as e:
        import traceback
        print(f"[_run_generate_lit] 錯誤：{traceback.format_exc()}")
        send_telegram("⚠️ 情感文學生成失敗，請稍後再試（/lit 重新生成）")
    finally:
        stop.set()


# ── 文字指令處理 ──────────────────────────────────────────────────

def cmd(text, command):
    return text == command or text.startswith(command + "@")


def handle_message(text):
    stories = get_today_stories()

    if cmd(text, "/help") or cmd(text, "/start"):
        send_telegram(
            "📖 小說機器人指令\n\n"
            "🔥 爽文模式（打臉逆襲）\n"
            "/now — 即時生成1篇爽文\n"
            "/list — 選頻道 → 選類別 → 生成\n"
            "/more — 從高分類別加推1篇\n\n"
            "📚 情感文學模式\n"
            "/lit — 即時生成1篇情感文學故事\n"
            "/litlist — 選情緒基調 → 選類別 → 生成\n\n"
            "📋 故事管理\n"
            "/today — 今日故事目錄\n"
            "/fav — 收藏故事\n"
            "/history — 瀏覽最近7日故事\n"
            "/stats — 各類別評分統計\n\n"
            "💡 打 / 可快速呼出所有指令"
        )
        return

    if cmd(text, "/now"):
        threading.Thread(target=_run_generate_one, args=(None, ""), daemon=True).start()
        return

    if cmd(text, "/lit"):
        threading.Thread(target=_run_generate_lit, args=(None,), daemon=True).start()
        return

    if cmd(text, "/list"):
        handle_list()
        return

    if cmd(text, "/litlist"):
        handle_litlist()
        return

    if cmd(text, "/more"):
        threading.Thread(target=_run_generate_one, args=(None, "[加推]"), daemon=True).start()
        return

    if cmd(text, "/stats"):
        handle_stats()
        return

    if cmd(text, "/today") or cmd(text, "/menu"):
        if stories:
            send_toc_menu(stories)
        else:
            send_telegram("今日未有故事，用 /now 或 /lit 即時生成。")
        return

    if cmd(text, "/fav"):
        handle_fav()
        return

    if cmd(text, "/history"):
        handle_history()
        return

    if cmd(text, "/pick"):
        genre_name = text.split(maxsplit=1)[1].strip() if len(text.split()) > 1 else ""
        if genre_name:
            threading.Thread(target=_run_generate_one, args=(genre_name, "[指定]"), daemon=True).start()
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
