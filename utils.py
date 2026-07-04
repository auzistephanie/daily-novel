"""共用工具函數：genre data I/O、Telegram 發送、目錄選單。"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import json as _json

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

_REDIS_KEY = "genre_data"


def _redis_url():
    return os.getenv("UPSTASH_REDIS_REST_URL", "").rstrip("/")

def _redis_headers():
    return {"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"}


# ── Genre Data ────────────────────────────────────────────────────

def load_genre_data() -> dict:
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["GET", _REDIS_KEY],
        timeout=10,
    )
    value = resp.json().get("result")
    if not value:
        return {"recent_genres": [], "ratings": {}}
    return _json.loads(value)


def save_genre_data(data: dict) -> None:
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SET", _REDIS_KEY, _json.dumps(data, ensure_ascii=False)],
        timeout=10,
    )


# ── DNA 防重複記錄 ────────────────────────────────────────────────

def load_recent_dna() -> dict:
    """讀取最近用過的 DNA 元素記錄（每個維度最多存 15 個）。"""
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["GET", "recent_dna"],
        timeout=10,
    )
    value = resp.json().get("result")
    if not value:
        return {}
    return _json.loads(value)


def save_recent_dna(data: dict) -> None:
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SET", "recent_dna", _json.dumps(data, ensure_ascii=False)],
        timeout=10,
    )


def save_story_dna(genre_name: str, dna: dict) -> None:
    """暫存某 genre 最近一篇故事的 DNA，供評分時查詢（TTL 7 日）。"""
    key = f"story_dna:{genre_name}"
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SET", key, _json.dumps(dna, ensure_ascii=False), "EX", 604800],
        timeout=10,
    )


def load_story_dna(genre_name: str) -> dict:
    """讀取指定 genre 最近一篇故事的 DNA。"""
    key = f"story_dna:{genre_name}"
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["GET", key],
        timeout=10,
    )
    value = resp.json().get("result")
    if not value:
        return {}
    return _json.loads(value)


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
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"Telegram 設定缺失: token={'SET' if token else 'MISSING'}, chat_id={'SET' if chat_id else 'MISSING'}")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = _split_text(text)
    for idx, chunk in enumerate(chunks):
        payload = {"chat_id": chat_id, "text": chunk}
        if reply_markup and idx == len(chunks) - 1:
            payload["reply_markup"] = reply_markup
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=15)
                if resp.ok:
                    print(f"Telegram 發送成功 chunk {idx+1}/{len(chunks)}")
                    break
                print(f"Telegram 發送失敗（第 {attempt} 次）: {resp.status_code} {resp.text}")
            except requests.RequestException as e:
                print(f"Telegram 請求異常（第 {attempt} 次）: {e}")


# ── Trending 素材抓取 ─────────────────────────────────────────────

def fetch_trending_topics(channel: str = "M") -> str:
    """
    抓取微博熱搜 + 用 DeepSeek 蒸餾成爽文素材提示。
    結果 cache 3 小時，唔係每次都打 API。
    channel: "M" 男頻 / "F" 女頻
    返回一段給 prompt 用的素材字串（失敗返回空字串）。
    """
    import time

    CACHE_FILE = BASE_DIR / "trending_cache.json"
    CACHE_TTL = 3 * 3600  # 3 小時

    # 讀 cache
    try:
        cache = _json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if time.time() - cache.get("timestamp", 0) < CACHE_TTL:
            result = cache.get(channel, "")
            if result:
                print(f"[trending] 用 cache ({channel})")
                return result
    except Exception:
        cache = {}

    # 抓微博熱搜
    hot_words = []
    try:
        resp = requests.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://weibo.com/",
            },
            timeout=8,
        )
        data = resp.json().get("data", {})
        for item in (data.get("realtime", []) + data.get("hotgov", []))[:30]:
            word = item.get("word", "")
            if word:
                hot_words.append(word)
        print(f"[trending] 微博熱搜抓到 {len(hot_words)} 條")
    except Exception as e:
        print(f"[trending] 微博熱搜抓取失敗：{e}")

    hot_words_text = "、".join(hot_words[:20]) if hot_words else "（暫無數據）"

    # 用 DeepSeek 蒸餾成男／女頻爽文素材
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

        result_m, result_f = "", ""
        for ch, label in [("M", "男頻爽文（打臉逆襲）"), ("F", "女頻言情（虐渣追悔）"), ("L", "情感文學（情緒共鳴、人情冷暖）")]:
            prompt = (
                f"今日微博熱搜熱詞（背景參考）：{hot_words_text}\n\n"
                f"結合以上熱詞 + 你對 2026 年中文短劇市場的最新了解，為「{label}」提供：\n"
                f"1. 3-5 個而家最紅的劇情套路或題材（一行一個）\n"
                f"2. 2-3 個可直接用入故事的具體細節或情境\n"
                f"   （例：最新流行身份設定、觀眾最 HIGH 的場景類型、爆款台詞風格）\n\n"
                f"要求：直接輸出，唔需要標題解釋，每條唔超過 30 字，總字數唔超過 200 字。"
            )
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=400,
            )
            text = resp.choices[0].message.content.strip()
            if ch == "M":
                result_m = text
            else:
                result_f = text
            print(f"[trending] DeepSeek 蒸餾完成 ({ch})")

        # 儲存 cache
        new_cache = {
            "M": result_m,
            "F": result_f,
            "timestamp": time.time(),
        }
        CACHE_FILE.write_text(_json.dumps(new_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        return new_cache.get(channel, "")

    except Exception as e:
        print(f"[trending] DeepSeek 蒸餾失敗：{e}")
        return ""


def save_story_to_disk(story: dict) -> None:
    """將故事追加到今日故事檔案（stories/YYYY-MM-DD.json）。"""
    from datetime import datetime
    stories_dir = BASE_DIR / "stories"
    stories_dir.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = stories_dir / f"{today}.json"
    if filepath.exists():
        with open(filepath, encoding="utf-8") as f:
            stories = _json.load(f)
    else:
        stories = []
    stories.append(story)
    filepath.write_text(_json.dumps(stories, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[save_story_to_disk] 已存 {today}.json，共 {len(stories)} 篇")


# ── 留存 Metrics I/O（Phase 3 追更數據）──────────────────────────
# 追蹤真實可量度嘅點擊事件（Telegram bot 冇「已讀」回執，量度唔到開篇率）
#   start    — 開一個新系列
#   continue — 撳「▶️下一集」/選擇掣，追多一集
#   choice   — 用選擇掣分支（continue 的子集）
#   complete — 系列追到終集
# 結構：{genre: {"start":n,"continue":n,"choice":n,"complete":n}}

def load_metrics() -> dict:
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["GET", "retention_metrics"],
        timeout=10,
    )
    value = resp.json().get("result")
    return _json.loads(value) if value else {}


def save_metrics(data: dict) -> None:
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SET", "retention_metrics", _json.dumps(data, ensure_ascii=False)],
        timeout=10,
    )


def record_metric(event: str, genre_name: str) -> None:
    """記一個留存事件（非致命，失敗唔影響主流程）。"""
    try:
        data = load_metrics()
        g = data.setdefault(genre_name, {"start": 0, "continue": 0, "choice": 0, "complete": 0})
        g[event] = g.get(event, 0) + 1
        save_metrics(data)
    except Exception as e:
        print(f"[record_metric] {event}/{genre_name} 失敗（非致命）：{e}")


# ── 連載系列 I/O（Phase 1 追更引擎）──────────────────────────────

def save_series(series: dict) -> None:
    """存／更新一個連載系列（Redis，TTL 30 日），並維護 ongoing/done 索引。"""
    key = f"series:{series['id']}"
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SET", key, _json.dumps(series, ensure_ascii=False), "EX", 2592000],
        timeout=10,
    )
    is_done = series.get("status") == "completed"
    # 加入對應索引集合
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SADD", "series:done" if is_done else "series:ongoing", series["id"]],
        timeout=10,
    )
    # 完結後由 ongoing 移除
    if is_done:
        requests.post(
            f"{_redis_url()}/",
            headers={**_redis_headers(), "Content-Type": "application/json"},
            json=["SREM", "series:ongoing", series["id"]],
            timeout=10,
        )


def load_series(series_id: str) -> dict:
    """讀取指定系列，找不到返回 {}。"""
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["GET", f"series:{series_id}"],
        timeout=10,
    )
    value = resp.json().get("result")
    return _json.loads(value) if value else {}


def delete_series(series_id: str) -> None:
    """刪走指定連載系列（DEL 個 series:{id} key + 由 ongoing/done 索引 SREM 走）。"""
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["DEL", f"series:{series_id}"],
        timeout=10,
    )
    for idx in ("series:ongoing", "series:done"):
        requests.post(
            f"{_redis_url()}/",
            headers={**_redis_headers(), "Content-Type": "application/json"},
            json=["SREM", idx, series_id],
            timeout=10,
        )


def clear_all_ongoing_series() -> int:
    """清走全部仍在追緊嘅連載系列（DEL 每個 series:{id} + 清走 series:ongoing 索引）。
    返回實際清走咗幾多個。"""
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SMEMBERS", "series:ongoing"],
        timeout=10,
    )
    ids = resp.json().get("result", []) or []
    for sid in ids:
        requests.post(
            f"{_redis_url()}/",
            headers={**_redis_headers(), "Content-Type": "application/json"},
            json=["DEL", f"series:{sid}"],
            timeout=10,
        )
    requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["DEL", "series:ongoing"],
        timeout=10,
    )
    return len(ids)


def list_ongoing_series() -> list:
    """列出所有仍在連載中的系列（供 /series 顯示，順道清走已完結的殘留 id）。"""
    resp = requests.post(
        f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SMEMBERS", "series:ongoing"],
        timeout=10,
    )
    ids = resp.json().get("result", []) or []
    out = []
    for sid in ids:
        s = load_series(sid)
        if s and s.get("status") == "ongoing":
            out.append(s)
        else:
            # 清理：已完結或過期的 id 由 ongoing 索引移除
            requests.post(
                f"{_redis_url()}/",
                headers={**_redis_headers(), "Content-Type": "application/json"},
                json=["SREM", "series:ongoing", sid],
                timeout=10,
            )
    return out


def send_toc_menu(stories_data: list) -> None:
    """發送今日故事目錄（可點擊的 inline keyboard）。📖=爽文 📚=情感文學"""
    keyboard = []
    for i, s in enumerate(stories_data, 1):
        icon = "📚" if s.get("type") == "lit" else "📖"
        keyboard.append([{
            "text": f"{icon} {i}.  {s['genre']}  ·  {s['character']['name']}",
            "callback_data": f"story_{i}"
        }])
    send_telegram(
        "📋 今日故事目錄\n點擊任何一篇即可重讀：",
        reply_markup={"inline_keyboard": keyboard}
    )
