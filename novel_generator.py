import random
import json
import requests
import os
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
STORIES_DIR = BASE_DIR / "stories"

from utils import (
    load_genre_data, save_genre_data,
    send_telegram, send_toc_menu,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
)

NUM_STORIES = 3  # 每次生成篇數，改呢度就夠

# ── 類別清單，想加就喺呢度加 ──────────────────────────────────────
GENRES = [
    {"name": "重生逆襲", "desc": "主角重生回過去，帶著前世記憶精準佈局，讓所有曾經背叛、踩過他的人一個個親眼見證自己的失敗"},
    {"name": "打臉爽文", "desc": "主角被全場最看不起，偏偏他手握王炸——每一記打臉都當眾發生，旁觀者從嘲笑到跌破眼鏡"},
    {"name": "職場逆襲", "desc": "被上司當眾羞辱開除的小職員，三個月後以甲方老闆身份重回舊公司簽下千萬合同"},
    {"name": "馬甲文", "desc": "主角頂級身份被層層隱藏，被人踩得越狠，揭開的那一刻就越震撼——讓所有人當場石化"},
    {"name": "系統流", "desc": "主角獲得神秘系統後一路碾壓，反派每次圍剿都是送人頭，升級爽點密集到停不下來"},
    {"name": "醫術流", "desc": "被嘲笑是江湖騙子的主角，在最關鍵的時刻妙手回春，讓在場所有人包括頂級專家跪地折服"},
    {"name": "商戰逆襲", "desc": "身無分文被掃地出門，靠一步步精準佈局吞下整個行業，讓當初踩過他的人成為他的手下敗將"},
    {"name": "豪門真假身份", "desc": "被當廢物養大的「棄子」，真實血脈揭露的那一刻，震驚的不只是反派，連旁觀者都嚇出冷汗"},
    {"name": "都市隱世強者", "desc": "退隱多年的頂尖強者回到都市，以最普通的身份生活，被逼出手時每次都是降維打擊"},
    {"name": "穿越古代稱霸", "desc": "現代人穿越古代，用降維知識碾壓所有人，從被人嘲笑的異類到令萬人臣服的霸主"},
    {"name": "鑑寶奇才", "desc": "被假專家當眾嘲笑的外行人，用一眼定真假的神級眼力，讓整個行業的權威集體顏面盡失"},
    {"name": "贅婿稱王", "desc": "被妻家全族當廢物踩在泥裡的入贅女婿，真實身價比整個妻族大一百倍，打臉從家宴打到整個商界"},
    {"name": "學霸裝弱", "desc": "故意偽裝差生的絕頂天才，忍到最後關頭才出手，一次碾壓讓所有質疑者集體沉默"},
    {"name": "末世崛起", "desc": "末世降臨後覺醒頂級異能，從被人欺負的弱者成為所有人爭相依附的末世之王"},
    {"name": "復仇歸來", "desc": "被至親背叛害至谷底，三年後強勢歸來，每一步都是精準復仇，讓對方求饒的模樣成為最大快慰"},
    {"name": "甜寵逆襲", "desc": "被所有人欺負的主角突然身後站了個護短到極致的強大伴侶，從此所有欺負過他的人都得加倍還回去"},
    {"name": "古言權謀", "desc": "以弱女子之身進入最危險的宮廷江湖，步步為營、以弱克強，最終笑到最後執掌天下"},
    {"name": "競技熱血", "desc": "被所有人斷定無緣頂尖的選手，用一場場逆轉勝利讓所有質疑者閉嘴，最終站上最高領獎台"},
    {"name": "玄學風水", "desc": "被當眾嘲笑是騙子的玄學大師，用一次次精準預言讓所有嘲笑者親眼見證自己有多無知"},
    {"name": "神豪撒幣", "desc": "主角突然坐擁千億，花錢如流水，讓每一個曾看不起他的人在金錢面前狠狠打臉自己"},
    {"name": "前任悔恨記", "desc": "被拋棄時一無所有，三年後成為對方高攀不起的存在，前任跪地哭求復合的場面就是最爽的結局"},
]
# ──────────────────────────────────────────────────────────────────

# ── 反派原型（越具體越欠打，打臉才越爽）──────────────────────────
VILLAINS = [
    "飛黃騰達後回來羞辱舊愛的前任，帶著新歡在主角面前炫耀",
    "仗著關係上位的勢利眼上司，習慣把底層員工當出氣筒",
    "視平民如草芥的富二代，出手就是羞辱，從不覺得自己有錯",
    "表裡不一的偽善閨蜜／兄弟，笑著背後捅刀最後還裝無辜",
    "以為自己最懂行的假專家，當眾嘲笑主角是外行是騙子",
    "豪門家族的勢利親戚，因為主角出身低微，當眾讓人難堪",
    "同學聚會上最愛炫耀的得意者，專門在舊同學面前踩低比較",
    "嫌貧愛富的岳父母家族，把入贅女婿當奴才使，隨時嘲諷奚落",
    "飛揚跋扈的大客戶，把服務人員當奴才，稍有不順就叫人滾蛋",
    "一直在主角面前踩低的競爭對手，靠資源優勢不斷打壓",
    "恩將仇報的白眼狼，被主角幫助過卻轉頭聯合外人對付主角",
    "狐假虎威的小人，靠攀附大樹就以為可以為所欲為",
]
# ──────────────────────────────────────────────────────────────────

SURNAMES = [
    "林", "陳", "張", "李", "王", "劉", "趙", "黃", "周", "吳",
    "徐", "孫", "馬", "朱", "胡", "郭", "何", "高", "羅", "鄭",
    "梁", "謝", "宋", "唐", "許", "韓", "馮", "鄧", "曹", "彭",
    "曾", "蕭", "田", "董", "袁", "潘", "蔣", "蔡", "余", "杜",
    "葉", "程", "魏", "蘇", "呂", "丁", "任", "盧", "姚", "崔",
    "江", "史", "顧", "邵", "薛", "雷", "賀", "龍", "傅", "錢",
    "秦", "尹", "廖", "鍾", "歐", "石", "方", "柳", "孔", "湯",
]
MALE_FIRST = [
    "浩然", "子軒", "宇辰", "逸飛", "煜城", "天明", "靖宇", "思遠",
    "楚風", "凌霄", "旭東", "澤宇", "景行", "翰林", "承志", "修遠",
    "道明", "炎龍", "寒星", "默言", "孤鶴", "雲起", "墨淵", "風行",
    "千塵", "一諾", "玄夜", "煊赫", "鈞天", "臨淵", "慕白", "北辰",
    "子衿", "長歌", "驚鴻", "望舒", "燭龍", "霽月", "扶搖", "淩雲",
    "錦年", "辭安", "予懷", "景澄", "明燭", "執筆", "問心", "向晚",
]
FEMALE_FIRST = [
    "若汐", "詩涵", "雨桐", "夢琪", "欣怡", "靜雯", "曉彤", "語嫣",
    "婉清", "芷若", "清歡", "霜華", "冷月", "暖陽", "素顏", "琳琅",
    "瑾瑜", "流光", "如意", "青鸞", "玉笙", "霓裳", "輕塵", "凌波",
    "傾城", "絕色", "冰魄", "紫蝶", "月華", "星眸", "初見", "驚鴻",
    "歲寧", "晚吟", "映雪", "聽荷", "煙柳", "雁回", "書雲", "夕顏",
    "錦繡", "辭月", "予安", "景晴", "明珠", "執念", "問雪", "向暖",
]
OCCUPATIONS = [
    "普通公司小職員", "剛畢業的實習生", "外賣配送員", "小區保安",
    "工廠普通工人", "來自農村的窮學生", "負債累累的失業者",
    "被公司辭退的前白領", "小診所實習醫生", "路邊小攤販",
    "快遞站分揀員", "便利店收銀員", "餐廳洗碗工", "建築工地小工",
    "剛被甩的落魄青年", "被家族放棄的邊緣人", "街頭流浪藝人",
    "圖書館兼職管理員", "廢品回收站工人", "夜市擺攤小販",
]
PERSONALITIES = [
    "表面廢柴實則頂級大佬", "腹黑低調不輕易出手",
    "毒舌但三觀極正", "天然呆外表下隱藏恐怖實力",
    "冷酷外表下有顆熱心腸", "被所有人小看的真正天才",
    "深不見底的隱藏強者", "笑面虎，笑著讓人絕望",
    "看似普通但底線不可碰，一碰就讓人後悔",
    "沉默寡言，出手即致命", "懶散外表下的頂級謀士",
    "被欺負慣了但某天突然開竅", "表面軟弱實則記仇記一輩子",
]
OPENING_HOOKS = [
    "主角在同學聚會上被眾人嘲笑混得最慘，就在這時他的手機響了",
    "前任帶著光鮮的新歡，親自來到主角工作的地方羞辱，當著所有人的面",
    "主角被上司當眾辱罵後宣布開除，保安押著他走出大樓，全公司圍觀",
    "主角被最信任的人當眾出賣，在最關鍵的場合被推入絕境",
    "主角只是想低調做事，卻被反派步步緊逼非要他出醜不可",
    "主角去高端場合辦事，被保安和服務員聯手以「不像有錢人」為由羞辱驅趕",
    "家族聚會上，所有親戚齊齊嘲笑主角一事無成，叫他不要給家族丟臉",
    "主角剛被掃地出門站在大樓門口，就遇上了昔日最瞧不起他的仇人",
    "一場公開競標上，反派大聲嘲笑主角沒資格坐在這裡，全場哄笑",
    "主角在醫院走廊被誤認為雜工，被傲慢的貴客當眾呼來喝去",
    "訂婚宴上，對方家族公然當著賓客面羞辱主角一家門第低賤，叫人難堪",
    "主角接到一通電話，對方的態度在三分鐘內從趾高氣揚到語氣顫抖",
]

RATING_LABELS = {1: "😞 差", 2: "😐 一般", 3: "😊 好", 4: "🤩 超好"}


# ── 類別記憶與加權選取 ────────────────────────────────────────────

def select_genres():
    data = load_genre_data()
    recent = data.get("recent_genres", [])
    ratings = data.get("ratings", {})
    session_size = NUM_STORIES

    weights = []
    for g in GENRES:
        name = g["name"]
        w = 1.0

        # 近期使用懲罰（越近越低）
        last_session = recent[-(session_size):]
        prev_session = recent[-(session_size * 2):-(session_size)]
        older = recent[:-(session_size * 2)] if len(recent) > session_size * 2 else []

        if name in last_session:
            w *= 0.05
        elif name in prev_session:
            w *= 0.25
        elif name in older:
            w *= 0.65

        # 評分懲罰
        genre_ratings = ratings.get(name, [])
        if len(genre_ratings) >= 2:
            avg = sum(genre_ratings) / len(genre_ratings)
            if avg < 2:
                w *= 0.15
            elif avg < 2.8:
                w *= 0.55
            elif avg >= 3.8:
                w *= 1.3  # 高分加分

        weights.append(max(w, 0.01))

    # 加權無重複抽樣
    available = list(GENRES)
    avail_weights = list(weights)
    selected = []
    for _ in range(NUM_STORIES):
        total = sum(avail_weights)
        r = random.uniform(0, total)
        cumulative = 0
        for i, (genre, wt) in enumerate(zip(available, avail_weights)):
            cumulative += wt
            if r <= cumulative:
                selected.append(genre)
                available.pop(i)
                avail_weights.pop(i)
                break

    return selected


def update_genre_history(selected_genre_names):
    data = load_genre_data()
    recent = data.get("recent_genres", [])
    recent.extend(selected_genre_names)
    data["recent_genres"] = recent[-(NUM_STORIES * 6):]  # 保留最近 6 次
    save_genre_data(data)


# ── 主角生成 ──────────────────────────────────────────────────────

def generate_character():
    gender = random.choice(["男", "女"])
    surname = random.choice(SURNAMES)
    firstname = random.choice(MALE_FIRST if gender == "男" else FEMALE_FIRST)
    if random.random() < 0.25:
        firstname = firstname[0]
    return {
        "name": surname + firstname,
        "gender": gender,
        "occupation": random.choice(OCCUPATIONS),
        "personality": random.choice(PERSONALITIES),
    }


# ── 故事生成 ──────────────────────────────────────────────────────

def load_winners():
    data = load_genre_data()
    return data.get("winners", {})


def save_winner(genre_name, opening, villain):
    data = load_genre_data()
    winners = data.setdefault("winners", {})
    entries = winners.setdefault(genre_name, [])
    entries.append({"opening": opening, "villain": villain})
    winners[genre_name] = entries[-5:]  # 保留最近5次高分設定
    save_genre_data(data)


def generate_story(genre, character, max_retries: int = 3):
    """生成故事，失敗最多重試 max_retries 次。"""
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    opening = random.choice(OPENING_HOOKS)
    villain = random.choice(VILLAINS)

    # 若此類型有高分歷史，加入一條參考提示
    winners = load_winners().get(genre["name"], [])
    winner_hint = ""
    if winners:
        ref = random.choice(winners)
        winner_hint = f"""
【⭐ 上次此類型獲最高評分的成功設定（參考風格，創作全新故事）】
開場情境：{ref['opening']}
反派設定：{ref['villain']}
→ 此類開場和反派設計曾引發強烈爽感，可沿用相近的張力結構"""

    prompt = f"""你是當今最頂尖的中文網絡爽文作家，熟讀所有打臉爽文精華，深諳讀者爽點所在。你的故事讓人看了第一段就放不下，每一個打臉場面都讓讀者想大喊「爽！」。

【本篇核心設定】
▸ 類型：{genre['name']} — {genre['desc']}
▸ 主角：{character['name']}（{character['gender']}／起點：{character['occupation']}／特質：{character['personality']}）
▸ 反派原型：{villain}
▸ 開場情境：{opening}{winner_hint}

━━━━━━━━ 爽文黃金四幕（必須嚴格執行）━━━━━━━━

【第一幕：點燃怒火】500字內完成
• 反派登場，台詞要具體刺耳：「就你這廢物？」「你算什麼東西，也配坐在這？」「快給我滾！」
• 現場必須有旁觀者，且初期旁觀者站反派那邊——嘲笑、起哄、或沉默當作默許
• 目標：讓讀者在500字內對反派恨之入骨，迫不及待想看他出醜

【第二幕：暗流湧動】蓄力張力
• 主角表面吃虧，內心沉穩如山——用細節或旁白透露主角真正的底牌
• 反派越囂張，埋下的伏筆越讓讀者心癢難耐
• 禁止：主角主動解釋自己身份或能力，讓事實說話

【第三幕：連環打臉】爽點核心，至少三波遞進
• 第一波：小震撼，讓反派和旁觀者開始感到不對勁
• 第二波：中震撼，旁觀者態度開始動搖，反派開始慌亂
• 第三波：終極震撼，必須有具體震撼數字或頭銜（「這筆合同是十六億」「他是……集團的實際控制人」「全球排名第三的……」）
• 旁觀者反應弧線：嘲笑→疑惑→失聲→倒吸冷氣→爭相道歉

【第四幕：收割終場】乾淨俐落
• 反派必須在眾目睽睽下出醜、道歉或跪求，不給台階，不留餘地
• 主角一句話封殺，不廢話，不解釋——留白比長篇大論更有力量
• 結局必須讓讀者拍手稱快，合上故事時心情暢快

━━━━━━━━ 寫作鐵律 ━━━━━━━━
✦ 對白是靈魂：反派台詞要刺耳具體，主角回擊要短促狠辣
✦ 旁觀者是放大鏡：他們的反應就是讀者情緒的鏡子，必不可少
✦ 節奏如海浪：衝突→短暫緩氣→更大衝突，一浪高過一浪
✦ 數字創造震撼：具體金額、具體頭銜、具體排名，比「非常有錢」強一百倍
✦ 嚴禁：冗長心理獨白、主角自我介紹身份、反派突然悔悟變好人、虎頭蛇尾的結局

字數：5500至7500字 ｜ 全文繁體中文 ｜ 直接從故事標題開始，無需前言

開始創作："""

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.2,
                max_tokens=9000,
            )
            return response.choices[0].message.content, villain, opening
        except Exception as e:
            last_err = e
            print(f"[generate_story] 第 {attempt} 次失敗：{e}")
    raise RuntimeError(f"生成失敗（已重試 {max_retries} 次）：{last_err}")


def generate_and_send_one(genre_name=None):
    """按需生成並發送單篇故事。genre_name 指定類型，None 則從高分類型中選。"""
    if genre_name:
        genre = next((g for g in GENRES if g["name"] == genre_name), None) or random.choice(GENRES)
    else:
        data = load_genre_data()
        ratings = data.get("ratings", {})
        recent = data.get("recent_genres", [])

        # 優先：高分類別（平均 ≥ 3.5，至少 2 次評分）
        favored = [
            g for g in GENRES
            if len(ratings.get(g["name"], [])) >= 2
            and sum(ratings[g["name"]]) / len(ratings[g["name"]]) >= 3.5
        ]
        if favored:
            genre = random.choice(favored)
        elif recent:
            # 次選：最久未出現的類別（LRU）
            recent_set = set(recent)
            unseen = [g for g in GENRES if g["name"] not in recent_set]
            genre = random.choice(unseen) if unseen else random.choice(GENRES)
        else:
            genre = random.choice(GENRES)

    character = generate_character()
    send_telegram(f"✨ 加推生成中：{genre['name']} ·  {character['name']}，請稍候...")

    content, villain, opening = generate_story(genre, character)
    header = (
        f"📖 [加推]  {genre['name']}\n"
        f"👤 {character['name']} · {character['gender']} · {character['occupation']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    rating_keyboard = {
        "inline_keyboard": [[
            {"text": "😞 差",   "callback_data": f"ratex_1_{genre['name']}"},
            {"text": "😐 一般", "callback_data": f"ratex_2_{genre['name']}"},
            {"text": "😊 好",   "callback_data": f"ratex_3_{genre['name']}"},
            {"text": "🤩 超好", "callback_data": f"ratex_4_{genre['name']}"},
        ]]
    }
    send_telegram(header + content, reply_markup=rating_keyboard)


# ── Telegram 快捷鍵盤 ─────────────────────────────────────────────

def send_reply_keyboard(num_stories: int = NUM_STORIES):
    buttons = [{"text": f"📖 故事{i}"} for i in range(1, num_stories + 1)]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for attempt in range(1, 4):
        try:
            resp = requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": "👇 快捷鍵盤，隨時一tap重讀",
                "reply_markup": {
                    "keyboard": [buttons],
                    "resize_keyboard": True,
                    "persistent": True,
                }
            }, timeout=15)
            if resp.ok:
                break
            print(f"send_reply_keyboard 失敗（第 {attempt} 次）: {resp.text}")
        except requests.RequestException as e:
            print(f"send_reply_keyboard 異常（第 {attempt} 次）: {e}")


def save_stories(stories_data):
    STORIES_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    with open(STORIES_DIR / f"{today}.json", "w", encoding="utf-8") as f:
        json.dump(stories_data, f, ensure_ascii=False, indent=2)


def cleanup_old_stories(keep_days: int = 30):
    """刪除超過 keep_days 日的故事存檔。"""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=keep_days)
    deleted = 0
    for f in STORIES_DIR.glob("*.json"):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d")
            if file_date < cutoff:
                f.unlink()
                deleted += 1
        except ValueError:
            pass
    if deleted:
        print(f"清理舊故事：已刪除 {deleted} 個存檔", flush=True)


# ── 主流程 ────────────────────────────────────────────────────────

def _generate_one(args):
    """ThreadPoolExecutor worker：生成單篇，回傳 (index, story_dict)。"""
    i, genre, character = args
    print(f"[{i}/{NUM_STORIES}] 生成：{genre['name']} | {character['name']}（{character['gender']}）...", flush=True)
    content, villain, opening = generate_story(genre, character)
    print(f"[{i}/{NUM_STORIES}] 完成 ✓", flush=True)
    return i, {
        "genre": genre["name"],
        "character": character,
        "content": content,
        "villain": villain,
        "opening": opening,
    }


def main():
    today = datetime.now().strftime("%Y年%m月%d日")
    send_telegram(f"📚 {today} 每日小說\n今日精選 {NUM_STORIES} 篇，生成中，請稍候...")

    selected_genres = select_genres()
    characters = [generate_character() for _ in selected_genres]

    # 平行生成所有故事
    tasks = [(i + 1, genre, char) for i, (genre, char) in enumerate(zip(selected_genres, characters))]
    stories_data = [None] * NUM_STORIES

    with ThreadPoolExecutor(max_workers=NUM_STORIES) as executor:
        futures = {executor.submit(_generate_one, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                idx, story = future.result()
                stories_data[idx - 1] = story
            except Exception as e:
                t = futures[future]
                print(f"[{t[0]}/{NUM_STORIES}] 生成失敗：{e}", flush=True)
                send_telegram(f"⚠️ 第 {t[0]} 篇《{t[1]['name']}》生成失敗：{e}")

    # 過濾失敗項，按順序發送
    # 注意：valid_stories 重新 enumerate，rating callback 對應新 index
    valid_stories = [s for s in stories_data if s is not None]
    if not valid_stories:
        send_telegram("⚠️ 今日所有故事均生成失敗，請稍後重試。")
        return

    for i, story in enumerate(valid_stories, 1):
        header = (
            f"📖 [{i}/{len(valid_stories)}]  {story['genre']}\n"
            f"👤 {story['character']['name']} · {story['character']['gender']} · {story['character']['occupation']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        # callback 用新 index（i），評分會正確對應 valid_stories[i-1]
        rating_keyboard = {
            "inline_keyboard": [[
                {"text": "😞 差",   "callback_data": f"rate_{i}_1"},
                {"text": "😐 一般", "callback_data": f"rate_{i}_2"},
                {"text": "😊 好",   "callback_data": f"rate_{i}_3"},
                {"text": "🤩 超好", "callback_data": f"rate_{i}_4"},
            ]]
        }
        send_telegram(header + story["content"], reply_markup=rating_keyboard)

    save_stories(valid_stories)
    update_genre_history([s["genre"] for s in valid_stories])
    send_toc_menu(valid_stories)
    send_reply_keyboard(len(valid_stories))
    cleanup_old_stories()
    print("完成 ✓")


if __name__ == "__main__":
    main()
