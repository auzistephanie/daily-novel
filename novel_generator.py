import random
import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

from utils import (
    load_genre_data, save_genre_data,
    send_telegram, send_toc_menu,
)

# ── 類別清單 ────────────────────────────────────────────────────────
# channel: "M" 男頻硬爽（三翻四抖打臉）｜ "F" 女頻言情（虐渣+追悔+雙向反轉）
# weight: 抽選權重，數字越大越常出。女頻為 2025 市場爆款，預設加重。
GENRES = [
    # ── 男頻（15）weight 1 ──
    {"name": "重生逆襲", "channel": "M", "weight": 1, "desc": "主角重生回過去，帶著前世記憶精準佈局，讓所有曾經背叛、踩過他的人一個個親眼見證自己的失敗"},
    {"name": "打臉爽文", "channel": "M", "weight": 1, "desc": "主角被全場最看不起，偏偏他手握王炸——每一記打臉都當眾發生，旁觀者從嘲笑到跌破眼鏡"},
    {"name": "職場逆襲", "channel": "M", "weight": 1, "desc": "被上司當眾羞辱開除的小職員，三個月後以甲方老闆身份重回舊公司簽下千萬合同"},
    {"name": "馬甲文", "channel": "M", "weight": 1, "desc": "主角頂級身份被層層隱藏，被人踩得越狠，揭開的那一刻就越震撼——讓所有人當場石化"},
    {"name": "系統流", "channel": "M", "weight": 1, "desc": "主角獲得神秘系統後一路碾壓，反派每次圍剿都是送人頭，升級爽點密集到停不下來"},
    {"name": "商戰逆襲", "channel": "M", "weight": 1, "desc": "身無分文被掃地出門，靠一步步精準佈局吞下整個行業，讓當初踩過他的人成為他的手下敗將"},
    {"name": "豪門真假身份", "channel": "M", "weight": 1, "desc": "被當廢物養大的「棄子」，真實血脈揭露的那一刻，震驚的不只是反派，連旁觀者都嚇出冷汗"},
    {"name": "都市隱世強者", "channel": "M", "weight": 1, "desc": "退隱多年的頂尖強者回到都市，以最普通的身份生活，被逼出手時每次都是降維打擊"},
    {"name": "穿越古代稱霸", "channel": "M", "weight": 1, "desc": "現代人穿越古代，用降維知識碾壓所有人，從被人嘲笑的異類到令萬人臣服的霸主"},
    {"name": "贅婿稱王", "channel": "M", "weight": 1, "desc": "被妻家全族當廢物踩在泥裡的入贅女婿，真實身價比整個妻族大一百倍，打臉從家宴打到整個商界"},
    {"name": "學霸裝弱", "channel": "M", "weight": 1, "desc": "故意偽裝差生的絕頂天才，忍到最後關頭才出手，一次碾壓讓所有質疑者集體沉默"},
    {"name": "復仇歸來", "channel": "M", "weight": 1, "desc": "被至親背叛害至谷底，三年後強勢歸來，每一步都是精準復仇，讓對方求饒的模樣成為最大快慰"},
    {"name": "甜寵逆襲", "channel": "M", "weight": 1, "desc": "被所有人欺負的主角突然身後站了個護短到極致的強大伴侶，從此所有欺負過他的人都得加倍還回去"},
    {"name": "玄學風水", "channel": "M", "weight": 1, "desc": "被當眾嘲笑是騙子的玄學大師，用一次次精準預言讓所有嘲笑者親眼見證自己有多無知"},
    {"name": "前任悔恨記", "channel": "M", "weight": 1, "desc": "被拋棄時一無所有，三年後成為對方高攀不起的存在，前任跪地哭求復合的場面就是最爽的結局"},
    # ── 女頻（10）weight 2 — 2025 市場爆款，加重 ──
    {"name": "追妻火葬場", "channel": "F", "weight": 2, "desc": "男主曾為白月光冷落／辜負女主，女主決絕轉身（重生／離婚／死遁）後，男主才驚覺失去摯愛，跪地追悔拼命挽回，卻已高攀不起"},
    {"name": "替嫁先婚後愛", "channel": "F", "weight": 2, "desc": "女主替姐妹／家族嫁入豪門或皇室，從相敬如冰、被冷待，到一步步攻陷高位男主的心，被寵上天"},
    {"name": "重生虐戀復仇", "channel": "F", "weight": 2, "desc": "女主帶前世記憶重生，前世被渣男綠茶害死，這一世步步算計手撕渣男賤女，反殺打臉，奪回屬於自己的一切"},
    {"name": "總裁甜寵", "channel": "F", "weight": 2, "desc": "看似普通的女主，身後站著護短到極致的腹黑霸總，誰欺負她就加倍奉還，寵到旁人羨慕嫉妒到發狂"},
    {"name": "雙重生", "channel": "F", "weight": 2, "desc": "男女主都帶記憶重生，這一世彼此試探、算計又奔赴，前世錯過的痛這一世全部補回，張力拉到最滿"},
    {"name": "馬甲千金", "channel": "F", "weight": 2, "desc": "被當鄉下廢物的女主，真實身份是頂級千金／影后／神醫／黑客大佬，一個個馬甲被踢爆，全場跪地震驚"},
    {"name": "死遁離婚", "channel": "F", "weight": 2, "desc": "女主受夠豪門委屈，假死或淨身出戶離開，男主才驚覺失去此生摯愛，瘋狂尋找、跪求回頭，女主早已雲淡風輕"},
    {"name": "穿書反派", "channel": "F", "weight": 2, "desc": "女主穿成書中註定慘死的炮灰／反派女配，憑藉先知逆天改命，避開原劇情死局，反引得男主真心傾慕"},
    {"name": "團寵真千金", "channel": "F", "weight": 2, "desc": "真假千金身份互換，真千金回歸豪門被全家團寵捧上天，假千金處處使壞卻被一次次當眾打臉揭穿"},
    {"name": "古言寵妃", "channel": "F", "weight": 2, "desc": "弱女子入宮或入王府，步步為營以柔克剛，從不受寵的棄妃一路逆襲成寵冠六宮、執掌鳳印的傳奇"},
]
# ──────────────────────────────────────────────────────────────────


def weighted_choice(genres):
    """按 genre 的 weight 加權隨機抽一個（女頻 weight 較高，較常出現）。"""
    if not genres:
        return random.choice(GENRES)
    weights = [g.get("weight", 1) for g in genres]
    return random.choices(genres, weights=weights, k=1)[0]

# ── 男頻反派原型（越具體越欠打，打臉才越爽）──────────────────────
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
    "裴", "沈", "白", "賈", "宋", "薑", "嚴", "武", "邱", "穆",
    "衛", "霍", "安", "喬", "祝", "卓", "尤", "凌", "宮", "祁",
]
# 複姓（約20%機率使用）
COMPOUND_SURNAMES = [
    "歐陽", "司馬", "上官", "慕容", "諸葛", "夏侯", "東方", "南宮",
    "北堂", "西門", "令狐", "獨孤", "軒轅", "皇甫", "長孫", "宇文",
    "赫連", "澹臺", "公孫", "百里",
]
MALE_FIRST = [
    "浩然", "子軒", "宇辰", "逸飛", "煜城", "天明", "靖宇", "思遠",
    "楚風", "凌霄", "旭東", "澤宇", "景行", "翰林", "承志", "修遠",
    "道明", "炎龍", "寒星", "默言", "孤鶴", "雲起", "墨淵", "風行",
    "千塵", "一諾", "玄夜", "煊赫", "鈞天", "臨淵", "慕白", "北辰",
    "子衿", "長歌", "驚鴻", "望舒", "燭龍", "霽月", "扶搖", "淩雲",
    "錦年", "辭安", "予懷", "景澄", "明燭", "執筆", "問心", "向晚",
    "子洵", "北野", "懷瑾", "斂辰", "夜澤", "雪霽", "霜離", "淵默",
    "南弦", "燎原", "奕辰", "朔風", "歸塵", "執白", "破軍", "定北",
]
# 男單字名
MALE_SINGLE = [
    "宸", "墨", "寒", "辰", "澈", "楠", "燁", "霆", "昀", "琛",
    "晁", "煜", "翊", "珩", "曜", "洵", "桓", "睿", "湛", "瀾",
]
# 男三字名（整體作為 first name，搭配單姓）
MALE_THREE_FIRST = [
    "白塵舊", "臨淵止", "一紙書", "笑蒼生", "問長歌", "執念深",
    "歸無期", "破萬卷", "凌雲志", "北辰寒",
]
FEMALE_FIRST = [
    "若汐", "詩涵", "雨桐", "夢琪", "欣怡", "靜雯", "曉彤", "語嫣",
    "婉清", "芷若", "清歡", "霜華", "冷月", "暖陽", "素顏", "琳琅",
    "瑾瑜", "流光", "如意", "青鸞", "玉笙", "霓裳", "輕塵", "凌波",
    "傾城", "絕色", "冰魄", "紫蝶", "月華", "星眸", "初見", "驚鴻",
    "歲寧", "晚吟", "映雪", "聽荷", "煙柳", "雁回", "書雲", "夕顏",
    "錦繡", "辭月", "予安", "景晴", "明珠", "執念", "問雪", "向暖",
    "折枝", "聽風", "覓渡", "斂芳", "夜未央", "煙雨濃", "思無邪",
    "知秋意", "撫琴聲", "照無眠", "春山暮", "碧雲天",
]
# 女單字名
FEMALE_SINGLE = [
    "錦", "瑾", "璃", "昭", "玥", "鸞", "媱", "瀾", "霜", "晴",
    "姝", "婧", "葳", "嫺", "婠", "珺", "嬋", "懿", "毓", "姮",
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

# ── 女頻專屬池（言情：虐渣 + 追悔 + 雙向反轉）──────────────────────
FEMALE_VILLAINS = [
    "高高在上的男主，為了白月光一次次冷落、踐踏女主的尊嚴",
    "笑裡藏刀的綠茶白月光，當眾扮柔弱搶走屬於女主的一切",
    "嫌貧愛富的豪門婆婆，處處刁難、當眾羞辱寒門出身的兒媳",
    "搶走女主未婚夫／身份／家產的偽善白蓮花妹妹，還倒打一耙裝可憐",
    "趾高氣揚的渣男前夫／前任，拋棄女主後帶著新歡回來炫耀",
    "佔盡資源卻一無是處的假千金，霸著女主的家當還反咬她是冒牌貨",
    "表面溫柔實則狠毒的繼母與繼妹，聯手把女主逼上絕路",
    "仗著家世瞧不起女主的勢利親戚，當眾斷言她攀不上高枝",
    "宮中囂張跋扈的寵妃／皇后，倚仗聖寵步步打壓初入宮的女主",
]
FEMALE_OCCUPATIONS = [
    "被冷落的豪門正妻", "替嫁入豪門的灰姑娘", "剛離婚淨身出戶的前妻",
    "回歸豪門的真千金", "被退婚的落魄名門小姐", "隱藏身份的頂級千金",
    "穿成炮灰女配的現代女白領", "重生歸來的復仇女主", "不受寵的冷宮棄妃",
    "馬甲滿身的低調神醫", "影后隱退後的素人馬甲", "被未婚夫退婚的相府嫡女",
    "豪門聯姻的政治籌碼", "被原生家庭吸血的扶弟魔長女", "假死重生的商界女王",
]
FEMALE_PERSONALITIES = [
    "表面柔弱實則清醒決絕", "外柔內剛、忍到極致一擊斃命",
    "高位千金扮豬吃老虎", "看似溫順實則步步算計的謀士型",
    "心冷如冰、誰負她她加倍奉還", "重生後再不卑微、活得肆意通透",
    "笑面藏刀、不動聲色報盡前世仇", "看淡情愛、把尊嚴擺第一",
    "知世故而不世故、有底線有手腕", "前世受盡委屈、這一世只為自己而活",
]
FEMALE_OPENING_HOOKS = [
    "離婚協議書遞到女主面前，男主以為她會哭鬧，她卻平靜簽了字轉身就走",
    "婚禮上男主當眾宣布只愛白月光，女主摘下婚戒微笑離場，全場譁然",
    "女主重生回到被害死的那一天，這一次她要親手把命運改寫",
    "豪門家宴上，全家嘲笑女主高攀，她淡淡亮出真正身份令滿座失聲",
    "白月光當眾羞辱女主是替代品，下一秒女主的天價身份被揭穿",
    "女主假死離開三年，再見時男主才驚覺自己親手弄丟了此生摯愛",
    "穿成書中註定慘死的炮灰女配，女主開局就決定改寫死局劇情",
    "繼妹搶走訂婚對象還當眾炫耀，女主卻收到神秘豪門的認親電話",
    "冷宮裡無人問津的棄妃，一夕之間成了皇帝跪求原諒的心頭硃砂",
    "男主帶著新歡回家逼女主讓位，她笑著遞上早已備好的離婚協議",
]

# ── 主角生成 ──────────────────────────────────────────────────────

def generate_character(channel="M"):
    """生成主角。channel='F' 女頻則以女主為主、配言情身份。"""
    if channel == "F":
        gender = "女" if random.random() < 0.9 else "男"
        occupation = random.choice(FEMALE_OCCUPATIONS)
        personality = random.choice(FEMALE_PERSONALITIES)
    else:
        gender = random.choice(["男", "女"])
        occupation = random.choice(OCCUPATIONS)
        personality = random.choice(PERSONALITIES)

    # 姓氏：20% 複姓，80% 單姓
    if random.random() < 0.20:
        surname = random.choice(COMPOUND_SURNAMES)
    else:
        surname = random.choice(SURNAMES)

    # 名字結構抽籤：
    # 單字名 20%、三字名 10%（只配單姓）、雙字名 70%
    roll = random.random()
    if roll < 0.20:
        # 單字名
        firstname = random.choice(MALE_SINGLE if gender == "男" else FEMALE_SINGLE)
    elif roll < 0.30 and len(surname) == 1:
        # 三字名（僅單姓）
        firstname = random.choice(MALE_THREE_FIRST if gender == "男" else FEMALE_FIRST[-12:])
    else:
        firstname = random.choice(MALE_FIRST if gender == "男" else FEMALE_FIRST)

    return {
        "name": surname + firstname,
        "gender": gender,
        "occupation": occupation,
        "personality": personality,
    }


# ── 故事生成 ──────────────────────────────────────────────────────

def load_winners():
    data = load_genre_data()
    return data.get("winners", {})


# ── 故事差異化元素池 ──────────────────────────────────────────────
STORY_SETTINGS = [
    "國際拍賣行的頂級藏品發布現場", "米芝蓮三星餐廳的包廂雅座",
    "豪華郵輪的頭等艙甲板", "跨國律師事務所的高管會議室",
    "奢侈品集團的全球董事局", "頂尖私立醫院的貴賓病房走廊",
    "知名大學的百年紀念典禮", "五星酒店的天台私人宴會廳",
    "古董珠寶拍賣發布會", "私人飛機的 VIP 候機室",
    "高端婚禮的戶外草坪儀式", "藝術品鑑定機構的展廳",
    "名流慈善晚宴的紅毯入口", "跨境電商的億元直播間",
    "國際馬場的 VIP 觀賽包廂", "私人遊艇的海上派對",
    "頂級私人會所的麻將室", "城市最高樓的觀景餐廳",
]
HIDDEN_IDENTITIES = [
    "跨國集團的實際控股幕後人", "業界最神秘的頂級操盤手",
    "三個月前已悄悄收購對方公司的真正老闆", "從不露面的傳奇神醫",
    "全球排名前三的黑客組織創辦人", "那家集團的獨生繼承人",
    "業界封神的設計大師真實身份", "失蹤十年的豪門家主嫡系",
    "看似普通卻持有對方公司三成股份", "連對方老闆都要親自赴約的神秘合作方",
    "政界最有影響力的幕後顧問之子女", "某頂級機構全球最年輕的合伙人",
]
REVERSAL_TRIGGERS = [
    "一通電話讓全場人臉色驟變", "一張簽名支票靜靜推過桌面",
    "手機螢幕上一個讓反派腿軟的聯絡人名字", "一個從門外走進來的神秘人認出了主角",
    "主角只說了一個數字，全場鴉雀無聲", "反派自己翻出的文件把自己打臉",
    "主角直接用流利外語接管了對話", "主角接過合約親筆簽下另一個更大的數字",
    "反派引以為傲的靠山，竟當場向主角彎腰", "一段現場直播意外捕捉了完整過程",
    "主角摘下帽沿，對方認出那張臉後說不出話", "主角的助理推門進來，帶來一份讓所有人失語的文件",
]
NARRATIVE_ANGLES = [
    "以現場旁觀者（服務員／保鏢）視角一鏡到底，見證全程反轉",
    "倒敘結構：開篇先呈現最震撼的結局一幕，再補述事件始末",
    "以反派的心理崩潰歷程為主線，從傲慢到恐慌到崩潰逐步推進",
    "雙線並行：主角暗中佈局 vs 反派步步進逼，最後一刻交匯引爆",
    "極簡旁白 + 密集對白：靠嘴炮和動作說話，心理描寫不超過全文10%",
    "先抑後揚：前三分之一把主角貶到谷底，後三分之二讓他/她一路踩臉上去",
]

def _pick_unique_elements():
    """每次生成時隨機抽取一組差異化元素，令每篇故事有獨特舞台與觸發點。"""
    return {
        "setting": random.choice(STORY_SETTINGS),
        "hidden_identity": random.choice(HIDDEN_IDENTITIES),
        "trigger": random.choice(REVERSAL_TRIGGERS),
        "angle": random.choice(NARRATIVE_ANGLES),
    }

# ── 爆款標題公式（男女頻共用）──────────────────────────────────────
TITLE_RULE = """【爆款標題公式 — 必做】
先在心中構思 3 個候選標題，揀張力最強嗰個做正式標題（只輸出最終一個）。
公式：[身份／情境鉤子]，[反轉／衝突結果]
要素：① 具體身份反差 ② 情緒鉤（悔／寵／虐／打臉） ③ 留懸念
範例：離婚後，夫人給總裁掛男科｜你另娶我他嫁，從此一別兩寬｜
     女將軍替嫁為皇后，暴君發現難招架｜重生歸來，醫妃斷絕滿門親情
禁止：四平八穩、無衝突、太文藝睇唔明"""


def _build_male_prompt(genre, character, villain, opening, winner_hint, unique):
    return f"""你是頂尖中文網絡爽文作家，深諳令讀者上癮的寫作技法。

【本篇設定】
類型：{genre['name']} — {genre['desc']}
主角：{character['name']}（{character['gender']}／{character['occupation']}／{character['personality']}）
反派：{villain}
開場情境：{opening}{winner_hint}

{TITLE_RULE}

【本篇獨特元素——必須融入，令故事有別於同類型】
故事舞台：{unique['setting']}
主角隱藏身份：{unique['hidden_identity']}
打臉觸發點：{unique['trigger']}
敘事風格：{unique['angle']}
⚠️ 以上四個元素必須有機融入情節，嚴禁套用「被羞辱→掏出名片→所有人跪地」的慣常公式

【核心寫法：三翻四抖】
爽文讓人追看的秘訣是「三翻四抖」——三次情勢反轉，四個震撼時刻，讓讀者情緒像過山車。

具體做法：
・裝逼是過程，打臉是高潮。主角越被看輕，翻身時越爽
・每次反轉都要比上一次更震撼，不能平鋪直敘
・震撼時刻用具體數字或身份：「這張支票是八千萬」比「很多錢」強一百倍
・反派的囂張程度決定打臉的爽感，要讓讀者恨到牙癢癢

【文字技法】
・段落控制在80字以內，短句製造節奏感
・多用動詞，少用形容詞——「他摔門而出」比「他非常憤怒地離開」有力十倍
・對白推進劇情，每句對白都要有目的，不說廢話
・感官細節製造代入感：聲音、表情、動作比心理描寫更抓人

【底線】
・開場立刻入題，不要鋪墊超過200字
・故事必須完整，主角大獲全勝後才結束
・嚴禁：長篇心理獨白、突然斷尾、反派莫名變好人
・結尾寧可簡單直接，也不要複雜模糊——主角贏了，反派輸了，一句話收尾，完整清晰

字數：2000至2500字 ｜ 繁體中文 ｜ 直接從標題開始

開始："""


def _build_female_prompt(genre, character, villain, opening, winner_hint, unique):
    return f"""你是頂尖中文網絡言情爽文作家，深諳令女性讀者上癮的「虐爽」技法。

【本篇設定】
類型：{genre['name']} — {genre['desc']}
女主：{character['name']}（{character['gender']}／{character['occupation']}／{character['personality']}）
反派：{villain}
開場情境：{opening}{winner_hint}

{TITLE_RULE}

【本篇獨特元素——必須融入，令故事有別於同類型】
故事舞台：{unique['setting']}
女主隱藏身份：{unique['hidden_identity']}
反轉觸發點：{unique['trigger']}
敘事風格：{unique['angle']}
⚠️ 以上四個元素必須有機融入情節，嚴禁套用「被羞辱→掏出身份→男主跪地求原諒」的慣常公式

【女頻核心爽點：虐渣 + 追悔 + 雙向反轉】
・前段虐：渣男賤女如何當眾踐踏女主尊嚴，越具體越欠揍，讓讀者恨到牙癢癢
・中段轉：女主決絕抽身，亮出隱藏身份／靠山／實力，全場震驚失聲
・後段爽：男主／反派追悔莫及、低頭跪求，女主雲淡風輕、高攀不起
・情緒張力 > 邏輯碾壓：靠表情、對白、反差場面推動，唔好長篇心理獨白

【文字技法】
・段落控制在80字以內，短句製造節奏感
・多用動詞，少用形容詞——「她摔門而出」比「她非常憤怒地離開」有力十倍
・對白推進劇情，每句對白都要有目的，金句收尾更抓人
・震撼用具體身份／數字：「她是顧氏唯一繼承人」比「她很厲害」強一百倍

【底線】
・開場立刻入題，不要鋪墊超過200字
・故事必須完整，女主大獲全勝／圓滿後才結束
・嚴禁：長篇心理獨白、突然斷尾、反派莫名洗白、女主聖母原諒
・結尾寧可簡單直接：女主贏了、活得漂亮，一句金句收尾，完整清晰

字數：2000至2500字 ｜ 繁體中文 ｜ 直接從標題開始

開始："""


def generate_story(genre, character, max_retries: int = 3):
    """生成故事，失敗最多重試 max_retries 次。按 genre channel 分男／女頻寫法。"""
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    channel = genre.get("channel", "M")
    if channel == "F":
        opening = random.choice(FEMALE_OPENING_HOOKS)
        villain = random.choice(FEMALE_VILLAINS)
    else:
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

    unique = _pick_unique_elements()
    if channel == "F":
        prompt = _build_female_prompt(genre, character, villain, opening, winner_hint, unique)
    else:
        prompt = _build_male_prompt(genre, character, villain, opening, winner_hint, unique)

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.1,
                max_tokens=5000,
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
            # 次選：最久未出現的類別（LRU），加權偏向女頻爆款
            recent_set = set(recent)
            unseen = [g for g in GENRES if g["name"] not in recent_set]
            genre = weighted_choice(unseen) if unseen else weighted_choice(GENRES)
        else:
            genre = weighted_choice(GENRES)

    character = generate_character(genre.get("channel", "M"))
    send_telegram(f"✨ 加推生成中：{genre['name']} ·  {character['name']}，請稍候...")

    content, villain, opening = generate_story(genre, character)
    print(f"[generate_and_send_one] 故事生成完成，字數={len(content)}")
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
    print(f"[generate_and_send_one] 準備發送，total_len={len(header + content)}")
    send_telegram(header + content, reply_markup=rating_keyboard)
    print("[generate_and_send_one] send_telegram 完成")


