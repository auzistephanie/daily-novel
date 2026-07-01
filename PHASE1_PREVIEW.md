# Phase 1 — 連載追更引擎（Code Preview · 未執行）

> 一個「系列」= 連續主角 + 世界觀 + 弧線（arc）。每集 800-1200 字，收喺 cliffhanger，
> Telegram 底部「▶️ 下一集」即時解鎖，追到 arc 完 →「🎬 開新系列」。
> **未改任何現有檔案；`/now` 單篇邏輯完全保留。**

---

## 資料模型（Redis，key = `series:{id}`，TTL 30 日）

```json
{
  "id": "s7f3a2",
  "genre": "追妻火葬場", "channel": "F",
  "character": { "name": "...", "gender": "女", "occupation": "...", "personality": "...", "wound": "..." },
  "title": "系列名（模型於第1集生成）",
  "arc": ["虐", "反擊", "揭底", "終局"],
  "dna": { ...一次抽好、全系列共用，保證風格連貫... },
  "episodes": [ { "ep": 1, "content": "...", "cliffhanger": "..." } ],
  "next_hook": "餵落一集嘅懸念種子",
  "status": "ongoing",
  "created": "2026-07-01T..."
}
```
Callback 用 `nextep_{id}` 攜帶 series id（<64 bytes，stateless）。

---

## 1) `novel_generator.py` — 新增（唔郁現有 function）

```python
# ── 系列弧線骨架池（每個 beat = 一集）──────────────────────────────
SERIES_ARCS = [
    {"name": "虐戀四幕", "channel": "F",
     "beats": ["當眾被虐、尊嚴被踐踏到底", "決絕轉身，亮出第一張底牌",
               "身份與真相層層揭開，全場震動", "終極反殺，對方跪地追悔莫及"]},
    {"name": "雙強五幕", "channel": "F",
     "beats": ["勢均力敵的初次交鋒", "彼此試探、暗中較勁", "危機逼近、被迫並肩",
               "最大反轉、關係翻盤", "雙向奔赴，各自封神"]},
    {"name": "逆襲五幕", "channel": "M",
     "beats": ["谷底受辱、萬人踩低", "暗中佈局初現端倪", "第一次當眾打臉",
               "反派反撲、危機升級", "全面碾壓、塵埃落定"]},
    {"name": "懸疑三幕", "channel": "F",
     "beats": ["迷局開場、拋出最大鉤子", "真相碎片、中段大反轉", "謎底爆發、情感與懸念同收"]},
    {"name": "腦洞末世四幕", "channel": "M",
     "beats": ["末世降臨、規則崩壞", "覺醒異能、第一次逆襲", "陣營對決、人性考驗", "登頂終局、改寫規則"]},
]

def _pick_arc(channel):
    pool = [a for a in SERIES_ARCS if a["channel"] == channel] or SERIES_ARCS
    return random.choice(pool)

# ── 單集 prompt（取代整篇完結；強制 cliffhanger + 控制區塊）──────────
def _build_episode_prompt(series, ep_num, unique, villain, trending_hint=""):
    beats = series["arc"]
    beat = beats[ep_num - 1]
    is_last = ep_num == len(beats)
    ch = series["channel"]
    c = series["character"]
    recap = "" if ep_num == 1 else f"\n【上集懸念（本集須接住並回應）】\n{series.get('next_hook','')}\n"
    style_line = _build_female_prompt if ch == "F" else _build_male_prompt  # 沿用同款語感條款
    tone = "女性讀者看完想截圖轉發的言情爽文" if ch == "F" else "讓人第一句就放不下的打臉逆襲爽文"

    ending_rule = (
        "【本集為最終集】完整收束 arc：反派下場交代清楚、主角最終狀態有畫面感、"
        "呼應第1集開場細節。結尾輸出一行控制碼：<<<END>>>"
        if is_last else
        "【本集非最終集】必須收喺 cliffhanger（一個逼讀者想睇下一集嘅懸念/反轉/未解場面），"
        "唔好把本 beat 的爽點一次過洩晒。結尾另起一行輸出控制碼："
        "<<<NEXT: 一句下集懸念種子（20字內，供下集接續，唔會顯示畀讀者）>>>"
    )
    title_rule = ("首集：於正文最上方寫出系列標題（爆款公式）。"
                  "另起一行輸出：<<<TITLE: 系列名>>>" if ep_num == 1 else "唔好再寫標題，直接接住劇情。")

    return f"""你是頂尖中文網絡爽文作家，寫緊一個連載系列嘅「第 {ep_num}/{len(beats)} 集」，{tone}。

【系列設定（全系列一致，唔可改）】
類型：{series['genre']}
主角：{c['name']}（{c['gender']}／{c['occupation']}／{c['personality']}）
個人傷口：{c['wound']}
反派原型：{villain}
故事舞台：{unique['setting']}
寫作風格（全系列統一）：{unique['writing_style']}
{recap}
【本集任務 — beat {ep_num}】
{beat}
→ 本集只推進呢一個 beat，唔好跳。節奏：每 200-300 字要有一個情緒點、資訊反轉或懸念，唔可以有悶場。

{title_rule}

{ending_rule}

【硬指標】
・第一段即入戲，接住上集張力（首集用開場鉤子）
・具體 > 籠統（數字、頭銜、實物）
・對白帶性格與潛台詞
・{'完整結局最少佔本集 30%' if is_last else '本集 800-1200 字，收尾必須吊人'}

字數：{'1200-1800（終集可長)' if is_last else '800-1200'} ｜ 繁體中文 ｜ 直接開始寫：
{('【今日爆款素材參考，自然融入1個】' + chr(10) + trending_hint) if trending_hint else ''}"""


# ── 控制碼解析 ────────────────────────────────────────────────────
import re
def _parse_episode(raw):
    title = None; next_hook = None; ended = False
    m = re.search(r"<<<TITLE:\s*(.+?)>>>", raw)
    if m: title = m.group(1).strip()
    m = re.search(r"<<<NEXT:\s*(.+?)>>>", raw)
    if m: next_hook = m.group(1).strip()
    if "<<<END>>>" in raw: ended = True
    clean = re.sub(r"<<<(TITLE|NEXT):.*?>>>", "", raw)
    clean = clean.replace("<<<END>>>", "").rstrip()
    return clean, title, next_hook, ended


# ── 開新系列 / 續集 ───────────────────────────────────────────────
def start_new_series(genre_name=None):
    from utils import save_series
    genre = (next((g for g in GENRES if g["name"] == genre_name), None)
             if genre_name else weighted_choice(GENRES))
    ch = genre.get("channel", "M")
    character = generate_character(ch, genre["name"])
    arc = _pick_arc(ch)
    unique = _pick_unique_elements(genre["name"])
    villain = random.choice(FEMALE_VILLAINS if ch == "F" else VILLAINS)
    import uuid
    series = {
        "id": "s" + uuid.uuid4().hex[:5], "genre": genre["name"], "channel": ch,
        "character": character, "title": None, "arc": arc["beats"], "arc_name": arc["name"],
        "dna": unique, "villain": villain, "episodes": [], "next_hook": "",
        "status": "ongoing",
    }
    _generate_and_send_episode(series, 1)
    return series

def continue_series(series_id):
    from utils import load_series
    series = load_series(series_id)
    if not series:
        send_telegram("⚠️ 搵唔到呢個系列（可能已過期），用 /series 開新一個。"); return
    if series.get("status") == "completed":
        send_telegram("🎬 呢個系列已完結！開下一個？（/series）"); return
    _generate_and_send_episode(series, len(series["episodes"]) + 1)

def _generate_and_send_episode(series, ep_num):
    from utils import save_series
    ch = series["channel"]; total = len(series["arc"])
    send_telegram(f"✨ 生成中：《{series.get('title') or series['genre']}》第 {ep_num}/{total} 集，請稍候…")
    trending = ""
    try:
        from utils import fetch_trending_topics; trending = fetch_trending_topics(ch)
    except Exception: pass
    prompt = _build_episode_prompt(series, ep_num, series["dna"], series["villain"], trending)
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    raw = client.chat.completions.create(
        model="deepseek-chat", messages=[{"role": "user", "content": prompt}],
        temperature=1.1, max_tokens=4000).choices[0].message.content
    clean, title, next_hook, ended = _parse_episode(raw)
    if ep_num == 1 and title: series["title"] = title
    series["episodes"].append({"ep": ep_num, "content": clean})
    series["next_hook"] = next_hook or series.get("next_hook", "")
    if ended or ep_num >= total: series["status"] = "completed"
    save_series(series)

    is_done = series["status"] == "completed"
    ch_tag = "💕 女頻" if ch == "F" else "🔥 男頻"
    header = (f"📖 《{series.get('title') or series['genre']}》 第 {ep_num}/{total} 集\n"
              f"👤 {series['character']['name']} ｜ {ch_tag} ｜ {series['arc_name']}\n"
              f"━━━━━━━━━━━━━━━━━━━━\n\n")
    if is_done:
        kb = {"inline_keyboard": [[{"text": "🎬 開新系列", "callback_data": "newseries"},
                                   {"text": "⭐ 收藏", "callback_data": f"favx_{series['genre']}"}]]}
        footer = "\n\n━━━━━━━━━\n🎬 本系列完結"
    else:
        kb = {"inline_keyboard": [[{"text": f"▶️ 下一集（{ep_num+1}/{total}）",
                                    "callback_data": f"nextep_{series['id']}"}],
                                  [{"text": "⭐ 收藏", "callback_data": f"favx_{series['genre']}"}]]}
        footer = f"\n\n━━━━━━━━━\n👇 追落去（{ep_num}/{total}）"
    send_telegram(header + clean + footer, reply_markup=kb)
```

## 2) `utils.py` — 新增（3 個細 function，同現有 Redis 寫法一致）

```python
def save_series(series: dict) -> None:
    key = f"series:{series['id']}"
    requests.post(f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SET", key, _json.dumps(series, ensure_ascii=False), "EX", 2592000], timeout=10)
    # 記入 ongoing 清單，供 /series 列出
    requests.post(f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SADD", "series:ongoing" if series.get("status")!="completed" else "series:done", series["id"]], timeout=10)

def load_series(series_id: str) -> dict:
    resp = requests.post(f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["GET", f"series:{series_id}"], timeout=10)
    v = resp.json().get("result"); return _json.loads(v) if v else {}

def list_ongoing_series() -> list:
    resp = requests.post(f"{_redis_url()}/",
        headers={**_redis_headers(), "Content-Type": "application/json"},
        json=["SMEMBERS", "series:ongoing"], timeout=10)
    ids = resp.json().get("result", []) or []
    out = []
    for sid in ids:
        s = load_series(sid)
        if s and s.get("status") == "ongoing": out.append(s)
    return out
```

## 3) `bot_listener.py` — 新增 handler + callback（3 處細改）

```python
# handle_callback 內新增兩個分支：
elif cb_data.startswith("nextep_"):
    sid = cb_data[7:]
    answer_callback(cb["id"], "生成下一集…")
    threading.Thread(target=_run_continue_series, args=(sid,), daemon=True).start()

elif cb_data == "newseries":
    answer_callback(cb["id"], "開新系列…")
    threading.Thread(target=_run_new_series, args=(None,), daemon=True).start()

# 新增執行緒 wrapper：
def _run_new_series(genre_name=None):
    stop = threading.Event(); threading.Thread(target=_typing_loop, args=(stop,), daemon=True).start()
    try:
        from novel_generator import start_new_series; start_new_series(genre_name)
    except Exception:
        import traceback; print(traceback.format_exc()); send_telegram("⚠️ 系列生成失敗，/series 再試")
    finally: stop.set()

def _run_continue_series(sid):
    stop = threading.Event(); threading.Thread(target=_typing_loop, args=(stop,), daemon=True).start()
    try:
        from novel_generator import continue_series; continue_series(sid)
    except Exception:
        import traceback; print(traceback.format_exc()); send_telegram("⚠️ 下一集生成失敗，再撳一次")
    finally: stop.set()

# handle_message 內新增 /series 指令：
if cmd(text, "/series"):
    ongoing = None
    try:
        from utils import list_ongoing_series; ongoing = list_ongoing_series()
    except Exception: pass
    if ongoing:
        kb = [[{"text": f"▶️ 續《{s.get('title') or s['genre']}》({len(s['episodes'])}/{len(s['arc'])})",
                "callback_data": f"nextep_{s['id']}"}] for s in ongoing[:8]]
        kb.append([{"text": "🎬 開全新系列", "callback_data": "newseries"}])
        send_telegram("📚 你追緊嘅系列：", reply_markup={"inline_keyboard": kb})
    else:
        threading.Thread(target=_run_new_series, args=(None,), daemon=True).start()
    return

# register_commands 加一行：{"command": "series", "description": "連載追更（開新／續集）"}
```

---

## 驗證計劃（我會用家身份實跑）
1. `start_new_series("追妻火葬場")` → 睇第 1 集有標題、收喺 cliffhanger、`<<<NEXT>>>` 正確解析、series 存入 Redis
2. `continue_series(id)` 連追 3 集 → 檢查劇情連貫、beat 逐集推進、字數 800-1200、最終集有完整結局 + `status=completed`
3. Telegram 實測「▶️ 下一集」按鈕 + `/series` 列表
4. 通過 → 更新 CLAUDE.md 改版歷史 → `python3 github_push.py`

---

## 出手前要你揀 2 個決定
見對話中嘅提問。confirm 後我即刻改 3 個檔案 + 實跑驗證。
