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
    {"name": "漫畫感爽文", "channel": "M", "weight": 2, "desc": "誇張反差到位、笑點密集、每一記打臉都帶著漫畫分鏡感，反派蠢得可愛主角強得荒謬，讓讀者邊笑邊爽"},
    {"name": "前任悔恨記", "channel": "M", "weight": 1, "desc": "被拋棄時一無所有，三年後成為對方高攀不起的存在，前任跪地哭求復合的場面就是最爽的結局"},
    {"name": "末世腦洞", "channel": "M", "weight": 2, "desc": "末世／規則崩壞突然降臨，主角憑冷靜與腦洞在絕境中覺醒異能，一步步逆襲登頂，改寫生存規則——2026 男頻腦洞末世爆點"},
    {"name": "都市情緒流", "channel": "M", "weight": 2, "desc": "都市小人物被生活與人情壓到谷底，一個轉折點爆發，用情緒張力帶動逆襲，讓讀者又心疼又解氣——2026 男頻都市情緒爆點"},
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
    {"name": "懸疑言情", "channel": "F", "weight": 2, "desc": "女主捲入一宗迷局——失憶、謀殺、身份置換或陰謀佈局——在解開謎底的過程中與男主從對立到相依，真相揭曉的瞬間情感與懸念同時爆發"},
    {"name": "雙強對峙", "channel": "F", "weight": 2, "desc": "女主唔係等被寵，係同男主勢均力敵——各有勢力手腕，初時對立互算，彼此試探又忍不住欣賞，最後雙向奔赴各自封神——2026 女頻由單強虐渣轉『雙強』爆點"},
]
# ──────────────────────────────────────────────────────────────────


def weighted_choice(genres):
    """按 genre 的 weight 加權隨機抽一個（女頻 weight 較高，較常出現）。"""
    if not genres:
        return random.choice(GENRES)
    weights = [g.get("weight", 1) for g in genres]
    return random.choices(genres, weights=weights, k=1)[0]


# ── 追更率驅動（Phase 3）──────────────────────────────────────────
def _retention_multiplier(genre_name, metrics=None):
    """按留存數據算一個 0.5–3.0 嘅加權倍數。數據唔夠（start<2）返 1.0。
    完讀率高、平均追更集數多 → 倍數大 → 更常被抽中。"""
    if metrics is None:
        try:
            from utils import load_metrics
            metrics = load_metrics()
        except Exception:
            metrics = {}
    m = metrics.get(genre_name)
    if not m or m.get("start", 0) < 2:
        return 1.0
    starts = m["start"]
    comp_rate = m.get("complete", 0) / starts            # 完讀率 0-1
    avg_eps = (starts + m.get("continue", 0)) / starts    # 平均追更集數 ≥1
    mult = 1.0 + 0.6 * comp_rate + 0.15 * max(0.0, avg_eps - 1)
    return max(0.5, min(3.0, mult))


def weighted_choice_retention(genres, metrics=None):
    """weighted_choice 的留存加權版：base weight × 追更率倍數。"""
    if not genres:
        genres = GENRES
    if metrics is None:
        try:
            from utils import load_metrics
            metrics = load_metrics()
        except Exception:
            metrics = {}
    weights = [g.get("weight", 1) * _retention_multiplier(g["name"], metrics) for g in genres]
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
    # 現代爽文風（帥氣大氣）
    "浩然", "子軒", "宇辰", "逸飛", "煜城", "天明", "靖宇", "思遠",
    "楚風", "凌霄", "旭東", "澤宇", "景行", "翰林", "承志", "修遠",
    "道明", "炎龍", "寒星", "默言", "孤鶴", "雲起", "墨淵", "風行",
    "一諾", "煊赫", "鈞天", "臨淵", "慕白", "北辰",
    "長歌", "驚鴻", "望舒", "燭龍", "霽月", "扶搖", "淩雲",
    "錦年", "辭安", "予懷", "景澄", "明燭",
    "時硯", "晏清", "容棠", "知行", "明澈",
    "子洵", "北野", "懷瑾", "斂辰", "夜澤", "雪霽", "霜離", "淵默",
    "南弦", "燎原", "奕辰", "朔風", "歸塵", "執白", "破軍", "定北",
    # 古言 / 宮廷風
    "承淵", "煜明", "景璋", "允塵", "昭烈", "玄鈞", "霆峰", "靖川",
    "懷瑾", "玉衡", "晟熙", "昱深", "宣晏", "廷玉", "璟珩", "徵羽",
    # 現代都市新潮
    "亦晨", "司辰", "顧深", "傅行", "沈聿", "江予", "裴晝", "唐礫",
    "謝聆", "陸珩", "秦岫", "賀鳴", "褚離", "姜洵", "喬嶼", "霍淵",
]
# 男單字名
MALE_SINGLE = [
    "宸", "墨", "寒", "辰", "澈", "楠", "燁", "霆", "昀", "琛",
    "晁", "煜", "翊", "珩", "曜", "洵", "桓", "睿", "湛", "瀾",
    "玨", "璿", "熠", "昶", "煊", "鉞", "琰", "璞", "嶼", "嶠",
]
# 男三字名（整體作為 first name，搭配單姓）
MALE_THREE_FIRST = [
    "子明澤", "承遠志", "晏清川", "容棠深", "時硯行", "明澈鋒",
    "予淵嶼", "慎之遠", "景寒川", "臨安渡", "知行遠", "書硯深",
]
FEMALE_FIRST = [
    # 現代言情風
    "若汐", "詩涵", "雨桐", "夢琪", "欣怡", "靜雯", "曉彤", "語嫣",
    "婉清", "芷若", "清歡", "霜華", "冷月", "暖陽", "琳琅",
    "瑾瑜", "流光", "如意", "青鸞", "玉笙", "霓裳", "輕塵", "凌波",
    "月華", "星眸", "初見", "驚鴻",
    "歲寧", "晚吟", "映雪", "聽荷", "煙柳", "雁回", "書雲", "夕顏",
    "錦繡", "辭月", "予安", "景晴", "明珠", "執念", "問雪", "向暖",
    "折枝", "聽風", "覓渡", "斂芳",
    "容舒", "時念", "澄心", "以衿", "初禾", "言蹊", "暮棠", "安頤",
    "言晏", "清逸", "暮染", "聽竹", "弄月",
    # 古言 / 宮廷風
    "芙蓉", "瑤華", "錦鸞", "雪鳶", "碧霞", "凝霜", "燕歸", "芳菲",
    "玉蘭", "珊瑚", "鳳儀", "昭華", "靖嫻", "婉儀", "麗華", "淑嫻",
    "柔嘉", "德音", "令儀", "毓秀", "嘉禧", "韶光", "沁雪", "瑤光",
    # 現代都市新潮
    "顧念", "沈緗", "江繁", "裴玨", "唐璿", "謝昭", "陸汐", "秦璃",
    "賀霜", "褚晴", "姜瑤", "喬桑", "霍錦", "傅眉", "司曉", "宋晞",
]
# 女單字名
FEMALE_SINGLE = [
    "錦", "瑾", "璃", "昭", "玥", "鸞", "媱", "瀾", "霜", "晴",
    "姝", "婧", "葳", "嫺", "婠", "珺", "嬋", "懿", "毓", "姮",
    "璇", "瑤", "熙", "曦", "嬈", "婕", "璐", "嫣", "娉", "韻",
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

# ── 主角個人傷口（令讀者入戲的情感細節）──────────────────────────────
# 不是「很慘」的標籤，是一個讀者說「我明白那種感覺」的具體時刻
MALE_WOUNDS = [
    "第一次被人當眾羞辱時，他環顧四周，沒有一個人跟他對視——他記住了每一張臉",
    "有一年他真的撐不住，幾乎開口說「我需要幫忙」，但對方的電話在他說出口前就掛了",
    "他存了三年的錢被最信任的人「借走」，對方到現在還覺得他不應該介意",
    "他做過最憋屈的事，是替人背了一個鍋，沉默受了委屈，因為他知道解釋沒有用",
    "最孤獨的那段日子，不是沒有人在身邊，是在一群人中間發現沒有人真的看見他",
    "他有一次努力到幾乎成了，把消息告訴他以為最在乎他的人——對方說「你這個也行啊」",
    "習慣什麼都一個人扛，不是天性，是因為有一次他說了「我很累」，對方說「誰不累」",
    "最難過那天他一個人坐了很久，翻了通訊錄，找不到一個可以打電話的人",
    "他被人誣陷時拿出了所有證據，沒有一個人願意看，他從此明白：清白要靠自己掙",
    "第一次感覺到世界不公平，不是因為輸了，而是因為他發現那個贏的人根本不值得贏",
]

FEMALE_WOUNDS = [
    "她發現背叛的那天，哭都沒有哭——不是不難過，是突然意識到，她一個人哭慣了",
    "她說過一句「我需要你」，那個人把這句話用了很多次，每次都是要挾她的籌碼",
    "最累那段時間，她習慣把門關好才讓自己難過，怕被人看見，也怕讓人覺得麻煩",
    "她替每個人算盡了後路，唯獨那一次沒算到自己——那次讓她付出了最大的代價",
    "最孤獨的不是一個人，而是哭著發了消息，對方說「你想太多了」",
    "有一段時間她每天假裝很好，因為她清楚：如果她垮了，沒有人撐得住那個局面",
    "她不是不懂得愛，是有一次全心全意給了出去，換回來的是「你太黏了」",
    "家裡最懂她的人早就不在了，所以她學會了不讓人懂她——懂了才知道怎麼傷她",
    "她做的那些犧牲，沒有一個人記得，但她一旦有一次沒做到，所有人都記得很清楚",
    "最難過的不是被背叛，是她發現自己早就知道，只是不願意相信——浪費了太多時間",
]

# ── 反派動機種子（令反派立體，越理解其邏輯越恨他）──────────────────────
# 反派有「可以理解但錯誤」的動機，比純壞人更讓讀者恨
VILLAIN_MOTIVATIONS = [
    "他從小被人踩低，第一次有了權力，就把所有的委屈加倍還給眼前的人——他只是不懂得把出氣對象選對",
    "他以為這個世界本來就是強者踩弱者，他只是在做每個有能力的人都在做的事——他的錯誤是遇上了主角",
    "他嫉妒主角，但他不承認，他把嫉妒包裝成蔑視，把打壓叫做「規矩」，說服自己出手是有道理的",
    "他有一個他在乎的人——父母、伴侶、或昔日恩人——他所有的惡都是為了那個人，只是手段選錯了",
    "他本來不壞，但有一次他手軟，被人踩過，從此他決定永遠不再手軟，哪怕眼前這個人根本無辜",
    "他代表的不只是他自己，他身後有一套他從未質疑過的「規則」：出身決定位置，弱者活該被淘汰",
    "他對主角並無深仇，只是主角擋了他的路，而他習慣了掃掉擋路的人——主角是倒楣的那一個",
    "他做的每一件壞事都有一個「合理」的解釋，他從未覺得自己有錯——這才是最讓人寒心的地方",
    "他曾經和主角處境相同，但他選擇了向強者妥協、踩低更弱的人，他恨主角是因為主角選了他沒選的路",
    "他知道自己在做什麼，他不在乎，因為他從來沒有為這種事付過代價——直到遇上主角",
]

# ── 意外反轉種子（打破「羞辱→忍→爆→勝」固定節奏，令讀者真正意外）────
# 每篇必選一個，在最意想不到的時機自然呈現
TWIST_SEEDS = [
    "主角在最高潮勝利的那一刻，沒有任何嘲諷，沒有任何表情——只是轉身走了。這個沉默比任何言語都更讓人窒息。",
    "打臉的那句話，不是主角親口說的——是一個反派從未放在眼裡的人站出來說了，而主角只是站在旁邊，什麼都沒有說。",
    "讀者以為最大的反派是某個人，但到最後才發現，真正讓主角傷得最深的，是一個故事裡幾乎沒出現過的人。",
    "主角贏了之後，做的第一件事不是任何人預料到的——那個選擇讓讀者重新理解了這個人到底在乎什麼。",
    "反派在最後做了一件出人意料的事——不是悔改，但也不是繼續作惡——讓讀者對他/她的判斷變得複雜，沒有辦法純粹恨。",
    "故事裡有一個看似多餘的人（侍應、路人、沉默的同事）。最後整個結局的關鍵，是因為這個人的一個微小選擇。",
    "主角最強的那張牌，從頭到尾都沒有出過。他/她用次一等的牌贏了——讀者才意識到，主角的格局遠不止如此。",
    "讀者以為主角已經原諒了某件事，或者忘了——但最後一個細節證明他/她從來沒有忘記，只是選擇了不說，因為不需要。",
    "主角勝利之後沉默了很長時間，不是後悔，是突然明白了一件事——比勝利本身更重要的東西，在這個過程中悄悄改變了。",
    "反派費盡心思設的局，最後被一個完全不相關的巧合打破——但仔細看，那個「巧合」其實是主角三年前種下的一粒種子。",
]

# ── 主角生成 ──────────────────────────────────────────────────────

# 古言宮廷男名
MALE_COURT_NAMES = ["承淵", "煜明", "景璋", "允塵", "昭烈", "玄鈞", "霆峰", "靖川",
                    "懷瑾", "玉衡", "晟熙", "昱深", "宣晏", "廷玉", "璟珩", "徵羽"]
# 古言宮廷女名
FEMALE_COURT_NAMES = ["芙蓉", "瑤華", "錦鸞", "雪鳶", "碧霞", "凝霜", "燕歸", "芳菲",
                      "玉蘭", "珊瑚", "鳳儀", "昭華", "靖嫻", "婉儀", "麗華", "淑嫻",
                      "柔嘉", "德音", "令儀", "毓秀", "嘉禧", "韶光", "沁雪", "瑤光"]


def generate_character(channel="M", genre_name=""):
    """生成主角。channel='F' 女頻則以女主為主、配言情身份。
    genre_name 用於按題材選取風格合適的名字。"""
    if channel == "F":
        gender = "女" if random.random() < 0.9 else "男"
        occupation = random.choice(FEMALE_OCCUPATIONS)
        personality = random.choice(FEMALE_PERSONALITIES)
        wound = random.choice(FEMALE_WOUNDS)
    else:
        gender = random.choice(["男", "女"])
        occupation = random.choice(OCCUPATIONS)
        personality = random.choice(PERSONALITIES)
        wound = random.choice(MALE_WOUNDS)

    # 判斷題材風格，選取對應名字池
    is_court = genre_name in ("穿越古代稱霸", "古言寵妃", "穿書反派")

    # 姓氏：20% 複姓（古言例外，一律用單姓）
    if not is_court and random.random() < 0.20:
        surname = random.choice(COMPOUND_SURNAMES)
    else:
        surname = random.choice(SURNAMES)

    # 名字池選擇
    if is_court:
        firstname = random.choice(MALE_COURT_NAMES if gender == "男" else FEMALE_COURT_NAMES)
    else:
        # 名字結構抽籤：單字名 20%、三字名 10%（只配單姓）、雙字名 70%
        roll = random.random()
        if roll < 0.20:
            firstname = random.choice(MALE_SINGLE if gender == "男" else FEMALE_SINGLE)
        elif roll < 0.30 and len(surname) == 1:
            firstname = random.choice(MALE_THREE_FIRST if gender == "男" else FEMALE_FIRST[-12:])
        else:
            firstname = random.choice(MALE_FIRST if gender == "男" else FEMALE_FIRST)

    return {
        "name": surname + firstname,
        "gender": gender,
        "occupation": occupation,
        "personality": personality,
        "wound": wound,
    }


# ── 故事生成 ──────────────────────────────────────────────────────

def load_winners():
    data = load_genre_data()
    return data.get("winners", {})


# ── 故事 DNA 元素池（令每篇有獨特骨架，唔係換湯不換藥）──────────

# 場景（具體舞台，影響氛圍和可用道具）
STORY_SETTINGS = [
    "國際藝術品拍賣行，現場直播，全球頂級買家齊聚",
    "米芝蓮三星餐廳的半封閉包廂，隔壁桌聽得一清二楚",
    "豪華郵輪的頂層甲板派對，無處可逃，所有人都是目擊者",
    "跨國律師事務所的玻璃會議室，城市全景落地窗為背景",
    "五星酒店天台的私人婚宴，數百名賓客同場",
    "私人飛機候機室的 VIP 貴賓廳，只有十幾個人",
    "名流慈善晚宴，記者在場，任何風吹草動都會上新聞",
    "知名大學的百年堂慶典禮，校友榜上的名字說明一切",
    "頂級私人馬場的 VIP 包廂，賽前的緊張等待",
    "古董珠寶鑑定行，一件真品能讓整間舖子閉嘴",
    "跨境電商億元直播間，幾十萬人實時在線圍觀",
    "城市地標頂層旋轉餐廳，整個城市在腳下",
    "私人遊艇的後甲板，離岸三海里，逃無可逃",
    "高端私立醫院貴賓病房走廊，生死面前身份最露底",
    "奢侈品集團的全球董事局，每一把椅子都代表幾億身家",
    "頂尖商學院的校友同學會，最愛比較當年誰混得最好",
]

# 諷刺結構（懲罰要和罪行相配，這是令故事有靈魂的關鍵）
IRONY_STRUCTURES = [
    "反派用來羞辱主角的那件事，最後成了打臉自己的最大武器",
    "反派越大聲嘲笑主角窮／弱，越多人目睹後來的逆轉，跌得越慘",
    "反派費盡心機趕走主角，結果親手把主角推向了更大的舞台",
    "反派引以為傲的靠山，恰好是主角最不需要解釋的那張底牌",
    "反派當眾宣稱主角沒資格，下一秒所有人才發現，有資格沒資格是主角說了算",
    "反派對主角的每一次刁難，都被主角悄悄變成了對付反派的籌碼",
    "反派以為踩死了一個無名之輩，沒想到那是他人生中踩過的最後一個人",
    "反派最驕傲的東西——公司、地位、靠山——一件一件在眾目睽睽下歸了主角",
    "反派嘲笑主角的那個「缺點」，恰恰是主角碾壓全場的真正原因",
]

# 主角王牌（多樣化：財富型／知識型／關係型／信息型／道德制高點型）
TRUMP_CARDS = [
    # ── 財富／資產型 ──
    "反派公司三個月前已被主角悄悄全資收購，反派至今渾然不知",
    "主角口袋裡那張名片，上面的頭銜讓反派的靠山當場改口叫「老闆」",
    "整棟大樓的產權人是主角，連物管保安都是主角的人",
    "主角靜靜翻開一份文件，上面是反派賴以為傲的公司——欠主角的債",

    # ── 知識／專業型 ──
    "主角用反派聽不懂的術語接過話頭，在場真正的行家全部起身鼓掌",
    "主角一開口說的第一句外語，讓現場唯一的外國合作方當場換了座位",
    "反派在台上引用的那個行業案例，主角正是當初最關鍵的決策人——他說了三個字，整個論述垮了",
    "那份被反派當殺手鐧的數據報告，每一個結論都建立在一個主角一眼看穿的致命錯誤假設上",
    "反派以為拿到了主角的技術核心，卻不知道那個版本已棄用兩年，真正的版本在另一個地方",

    # ── 關係型 ──
    "主角把手機遞過去，讓反派看未接來電的號碼——那是反派最怕的名字",
    "反派費盡心思拿下的合同，主角一個電話就能讓對方撤回",
    "反派全程當作空氣的那個坐在角落的人，是今天唯一能拍板的決策者——主角的舊同學",
    "反派的新靠山電話打進來，卻叫反派先出去——因為電話那頭要先和主角說話",

    # ── 信息／掌控型 ──
    "反派的財務漏洞，主角三年前就掌握，只是一直沒用",
    "反派精心準備的報告，裡面每一個數字都是主角故意放出去的假情報",
    "那份反派以為已經銷毀的備份，主角在事發當晚就轉存在雲端，從未動過",
    "反派以為在說悄悄話，沒意識到主角剛才開著擴音——整個辦公室都聽見了",

    # ── 道德制高點型 ──
    "主角把自己被陷害的三年，用一張時間線說清楚——每一個節點都有在場的人可以當場核實",
    "主角說：『我沒有錄音，沒有截圖，我只是把你說過的話，在你說的那些人面前再說一遍』",
    "主角兩年前投資的一個不起眼項目，上週完成了三十億融資，但他一個字都沒提過",
]

# 反派致命弱點（決定其下場的根本原因，令結局有因果感）
VILLAIN_FLAWS = [
    "太愛當眾表演，選了人最多的場合出手，等於幫主角備了最多目擊者",
    "太輕視主角，連基本背調都懶得做，一無所知地撞上了槍口",
    "太貪心，同時得罪了所有盟友，打臉那刻沒有一個人站出來幫",
    "太依賴靠山，靠山一倒，立刻從老虎變成了被圍觀的貓",
    "習慣用錢和勢欺人，偏偏遇上一個根本不在乎這兩樣東西的主角",
    "以為沉默等於軟弱，把主角的每一次忍讓都誤判為懦弱",
    "太享受羞辱的過程，拖得太長，給了主角充分準備的時間",
    "不知道主角一直都知道他們的秘密，每一步都走在主角預設的棋局裡",
]

# 情感核心（令讀者在乎主角，這篇故事讓讀者最終帶走的情緒）
EMOTIONAL_CORES = [
    "心疼：主角默默扛著一切，從不解釋，從不喊冤，只是在等",
    "解氣：反派壞得剛剛好，主角贏得剛剛好，一點都不多，一點都不少",
    "震撼：讀者以為猜到了結局，但主角的反擊方式完全出乎意料",
    "唏噓：原來一切都是命運的伏筆，所有人的位置在開場就已注定",
    "爽快：主角每一句話都像一把刀，插進去再慢慢轉，讓反派無從反駁",
    "欽佩：主角不是靠運氣翻身，是靠格局和耐心贏得了所有人的尊重",
    "痛快：反派最自豪的東西，成了壓垮自己的最後一根稻草",
]

# 點睛之筆（一個開場細節，結尾賦予新含義，令故事有靈魂）
MEMORABLE_DETAILS = [
    "開場主角被嘲笑的那個細節（一件舊外套、一雙磨損的鞋、一個便宜的手機），結尾有了全新的意義",
    "反派開場說的那句嘲諷，在結局被主角原話奉還，語氣截然不同",
    "一個看似無關緊要的路人（侍應、清潔工、小孩），最後成了最關鍵的目擊者或轉折點",
    "主角全程沒有一次憤怒，越冷靜越讓反派發毛，最後反派比主角先崩潰",
    "主角開場做的一個不起眼的小動作（簽名、點菜、接電話），結尾才揭示那個動作的重量",
    "一個數字在開場出現過（價格、時間、樓層），結尾時這個數字代表了完全不同的東西",
    "主角有一個習慣性小動作，恰好成了識別真實身份的唯一線索",
]

# 寫作風格（參考 2025-26 頂流網文風格特徵，令每篇讀感截然不同）
WRITING_STYLES = [
    "短句炸彈風：每段最後一句必須是爆點。句子平均不超過15字，多用感歎句和問句製造懸念，讀者在手機上刷得根本停不下來",
    "瘋批戲謔風：敘述者帶著一絲戲謔看待一切，對白尖銳帶刺，幽默與殘忍並存——主角的每一句話都像說給旁觀者聽，讓讀者又爽又後怕",
    "細節電影風：靠具體感官細節（衣料觸感、空氣氣味、燈光角度、玻璃反光）建立臨場感，場景如同電影鏡頭，一個細節抵萬句旁白",
    "對白驅動風：70%靠對話推進，每句對白都有資訊、性格、潛台詞——主角說的話帶雙重含義，讀者第二遍才看懂全部",
    "情緒壓縮風：把五萬字的情緒濃縮進三千字，每一段都是情緒升壓閥，讀者看完覺得心臟被人握過——長句堆情緒，短句斬情緒",
    "金句密度風：每三段必有一句讓讀者想截圖的金句，要精準、狠、帶點哲理——對白金句優先，旁白金句收尾，轉發率第一",
    "多線蒙太奇風：在兩三個場景間快速切換，用電影剪接式節奏製造張力，讓讀者在拼圖過程中獲得成就感，最後一刻所有線索交匯",
]

# ── 懸念鉤子（令讀者在中段忍不住繼續看的關鍵時刻）────────────────────
# 植入故事中段（前半結束前），製造「必須睇完」的張力
SUSPENSE_HOOKS = [
    "主角做了一個動作，讀者看到，但場景裡沒有人看到——這個「秘密」讓讀者忍不住替主角緊張",
    "反派在某個關鍵時刻突然停下來，表情變了——他發現了什麼，但沒有說出來，讀者和主角都不知道他知道了什麼",
    "一個本來不重要的細節（一個名字、一份文件、一個眼神）在中段突然變得意味深長，讀者回頭想第一幕",
    "主角的計劃在中段遇上一個意外的變數——不是反派的計謀，是一個誰都沒料到的第三方",
    "故事進行到一半，主角說了一句話，讀者意識到他/她早就知道結局——但為什麼還要走這一步？",
    "反派在中段做了一件「好事」，讓讀者的情緒突然複雜起來，不確定接下來要怎麼想",
    "中段出現一個新角色，三言兩語就讓讀者感覺到：這個人的出現，會改變一切",
    "主角在勝利前夕，有一個短暫的猶豫——不是害怕，是想到了什麼，但沒有解釋，讀者帶著這個疑問看完後半",
    "反派的「最後底牌」在中段意外暴露——但主角的反應讓讀者意識到，這張牌根本打不中",
    "中段有一句話，第一次看以為是閒筆，看完全篇才明白，那句話是整個故事最重要的一句",
]

# 結局結構（明確收尾節奏，杜絕草率結束）
ENDING_STRUCTURES = [
    "回響呼應型：結尾主動呼應開場某個具體細節（一句話、一個動作、一件物品），讓讀者恍然大悟「原來早有伏筆」，合上手機還在回味",
    "轉身不回頭型：主角做完最後一件事，轉身離去——反派在背後意識到一切無法挽回，最後用旁觀者眼睛定格這個畫面，餘韻比言語深",
    "未來快閃型：主角離場後，用100-150字快閃交代三個月後／一年後的結果，每一筆都是對反派的補刀，最後一句定格主角最好的狀態",
    "金句收尾型：整篇最後一句必須是讓讀者想截圖轉發的話——主角親口說，或敘述者旁白，要精準、有力、帶點哲理，令全篇昇華",
    "旁觀者定格型：以在場第三方（侍應、助理、記者、路人）視角，記錄主角離場時的最後一個畫面，留白處比說出來更有力量",
    "雙重反轉型：讀者以為故事結束了，最後一段再給一個小反轉（一句話、一個細節），讓人「原來還有這個」的驚喜感，意猶未盡",
]

# ── 古言題材識別（用於場景、王牌分流）────────────────────────────
ANCIENT_GENRES = {"穿越古代稱霸", "古言寵妃"}

# 古言專屬場景（只用於 ANCIENT_GENRES，不與現代場景混用）
ANCIENT_SETTINGS = [
    "金碧輝煌的正殿大朝，文武百官肅立，史官執筆記錄每一句話",
    "皇后鳳儀宮的賜宴，後妃命婦雲集，一個眼神足以定人沉浮",
    "邊關中軍大帳，將士列陣，主帥一道軍令足以左右萬人生死",
    "禮部主持的殿試放榜，天子親臨，一篇文章可直達天聽改寫命運",
    "王府議事廳，幕僚謀士齊聚，一份密折可以扭轉整個朝堂格局",
    "御花園的春日賞梅宴，看似閒情雅致，暗中每句話都是試探",
    "宗廟祭典的莊嚴儀制，任何失禮都會被永久記入史冊",
    "皇城外的集市茶樓，消息在此集散，今日傳言明日便成聖旨",
]

# 古言專屬王牌（場景合理、有宮廷因果感）
ANCIENT_TRUMP_CARDS = [
    "主角袖中握著先帝親筆手諭，比任何人的靠山都硬三分",
    "那塊玉牌靜靜壓在案上，是連皇上都要禮讓的鐵卷丹書",
    "主角從容報出師門，在場所有人的靠山在那個名號面前退了半步",
    "反派最驕傲的靠山大人，此刻正向主角行禮——主角才是他真正效忠的主君",
    "主角攤開輿圖，指出反派引以為傲的計策——三年前已被識破，且留了後手",
    "主角拿出那份族譜，上面的血脈讓反派當場說不出話",
    "主角一紙薦書，出自當朝最不可得罪之人的親筆，讓反派所有佈局頃刻瓦解",
]

# 敘事結構（令每篇有不同的閱讀節奏）
NARRATIVE_STRUCTURES = [
    "順敘強化法：每個場景比上一個更緊張，壓力不斷升高直到爆發",
    "倒敘開場：第一段直接呈現反轉高潮的一個細節，再倒回去補述始末",
    "旁觀者視角：以在場的第三方（侍應、助理、路人）眼睛記錄全程，增加現場感",
    "反派主觀視角：跟隨反派從傲慢到困惑到恐慌到崩潰的心理歷程",
    "雙線剪接：主角暗中佈局 vs 反派步步緊逼，最後一刻兩條線交匯爆炸",
    "極簡敘述：旁白壓到最少，靠對話和行動推進，讓讀者自己感受",
]


def _pick_unique_elements(genre_name=""):
    """每次生成時隨機抽取一組故事 DNA，自動避開最近用過的元素（防重複）。
    genre_name 用於識別古言題材，自動切換對應場景／王牌池，避免古代現代混用。"""
    from utils import load_recent_dna, save_recent_dna

    try:
        recent = load_recent_dna()
    except Exception:
        recent = {}

    WINDOW = 5  # 每個維度記住最近 5 個，避免短期重複
    is_ancient = genre_name in ANCIENT_GENRES

    def pick_fresh(pool, key):
        used = set(recent.get(key, []))
        fresh = [x for x in pool if x not in used]
        if not fresh:        # 全部用過就重置
            fresh = pool
        return random.choice(fresh)

    unique = {
        "setting":            pick_fresh(ANCIENT_SETTINGS if is_ancient else STORY_SETTINGS, "setting"),
        "irony":              pick_fresh(IRONY_STRUCTURES,       "irony"),
        "trump_card":         pick_fresh(ANCIENT_TRUMP_CARDS if is_ancient else TRUMP_CARDS, "trump_card"),
        "villain_flaw":       pick_fresh(VILLAIN_FLAWS,          "villain_flaw"),
        "villain_motivation": pick_fresh(VILLAIN_MOTIVATIONS,    "villain_motivation"),
        "emotional_core":     pick_fresh(EMOTIONAL_CORES,        "emotional_core"),
        "memorable":          pick_fresh(MEMORABLE_DETAILS,      "memorable"),
        "structure":          pick_fresh(NARRATIVE_STRUCTURES,   "structure"),
        "writing_style":      pick_fresh(WRITING_STYLES,         "writing_style"),
        "ending":             pick_fresh(ENDING_STRUCTURES,      "ending"),
        "twist_seed":         pick_fresh(TWIST_SEEDS,            "twist_seed"),
        "suspense_hook":      pick_fresh(SUSPENSE_HOOKS,         "suspense_hook"),
    }

    # 更新 recent 記錄（sliding window）
    for key, val in unique.items():
        lst = recent.get(key, [])
        if val in lst:
            lst.remove(val)
        lst.append(val)
        recent[key] = lst[-WINDOW:]

    try:
        save_recent_dna(recent)
    except Exception:
        pass

    return unique

# ── 爆款標題公式（男女頻共用）──────────────────────────────────────
TITLE_RULE = """【爆款標題公式 — 必做】
先在心中構思 3 個候選標題，揀張力最強嗰個做正式標題（只輸出最終一個）。
公式：[身份／情境鉤子]，[反轉／衝突結果]
要素：① 具體身份反差 ② 情緒鉤（悔／寵／虐／打臉） ③ 留懸念
範例：離婚後，夫人給總裁掛男科｜你另娶我他嫁，從此一別兩寬｜
     女將軍替嫁為皇后，暴君發現難招架｜重生歸來，醫妃斷絕滿門親情
禁止：四平八穩、無衝突、太文藝睇唔明"""

# ── 鉤子密度規則（短劇節奏，Phase 2）──────────────────────────────
# 令單篇都有短劇「密集反轉」節奏，唔止頭尾有鉤子
HOOK_DENSITY_RULE = """【鉤子密度 — 短劇節奏硬指標】
每 200-300 字必須有一個「鉤」：一個情緒點、一個小反轉、一個新資訊、或一句令人想睇落去的懸念。
唔可以有連續兩三段都係平鋪直敘嘅過場。讀者喺手機碌，任何一段悶咗就會走——每一段都要有理由睇落下一段。"""


def _build_male_prompt(genre, character, villain, opening, winner_hint, unique, trending_hint=""):
    _trend = (
        f"\n【🔥 今日爆款素材參考（從實時熱搜蒸餾，自然融入 1-2 個最合適的，唔需要強塞）】\n{trending_hint}\n"
        if trending_hint else ""
    )
    return f"""你是頂尖中文網絡爽文作家，你的故事能讓讀者看第一句就放不下。

══════════════════════════════════
第一步：先在腦海中完成以下故事設計（不輸出這部分）
══════════════════════════════════

① 開場鉤子（第一句）
   必須是一句讓人無法停下來的話。
   好的鉤子範例：「那天他被人拖出大樓的時候，電梯裡站著的是他剛剛收購這棟大樓的律師。」
   測試標準：看完第一句，讀者必須想看第二句。

② 諷刺結構設計（靈魂所在）
   反派的「原罪」是什麼？
   懲罰如何與原罪精準對應，形成諷刺？
   例：反派用「你沒資格坐在這裡」羞辱主角 → 結局是主角買下這個場地，反派才是那個沒資格的人。
   本篇諷刺結構參考：{unique['irony']}

③ 主角王牌設計
   要夠具體，有震撼力，和場景有機結合。
   參考方向：{unique['trump_card']}

④ 反派設計（命門 + 動機）
   反派為何必敗？要有邏輯，不能只是「主角強」。
   命門參考：{unique['villain_flaw']}
   動機參考：{unique['villain_motivation']}
   → 反派要「可以理解但做錯了」——讀者越理解他的邏輯，越恨他的選擇，打臉才更有力

⑤ 懸念鉤子（讓讀者在中段放不下手機）
   在故事前半結束前植入：{unique['suspense_hook']}
   → 這個時刻要讓讀者產生「一定要看完」的感覺，不能提前解答

⑦ 點睛之筆（令故事有靈魂）
   在開場埋下一個細節，結尾賦予它完全不同的意義。
   參考：{unique['memorable']}

⑧ 情感核心（讀者帶走什麼感受）
   {unique['emotional_core']}

⑨ 主角的個人傷口（讓讀者真正心疼的那一刻）
   {character['wound']}
   → 開場前三分之一自然埋入，不需要旁白解釋，一個動作或細節就夠

⑩ 本篇意外反轉種子
   {unique['twist_seed']}
   → 在最意想不到的時機植入，不要提前預告

══════════════════════════════════
第二步：按以下設定寫正文
══════════════════════════════════

【本篇設定】
類型：{genre['name']} — {genre['desc']}
主角：{character['name']}（{character['gender']}／{character['occupation']}／{character['personality']}）
個人傷口：{character['wound']}
反派原型：{villain}
開場情境：{opening}
故事舞台：{unique['setting']}
敘事結構：{unique['structure']}{winner_hint}

{TITLE_RULE}

【本篇寫作風格 — 貫穿全文】
{unique['writing_style']}
→ 這是本篇的語感基調，從第一句到最後一句都要符合這個風格

{HOOK_DENSITY_RULE}

【反派動機——讓讀者理解但更恨他】
{unique['villain_motivation']}
→ 反派不能只是「壞」，要讓讀者看懂他為何這樣做，然後更恨他選錯了方式

【懸念鉤子——讓讀者在中段放不下】
{unique['suspense_hook']}
→ 在故事前半結束前自然植入，製造「必須看完」的張力，不能提前解答

【意外反轉種子——打破讀者預期】
{unique['twist_seed']}
→ 在最意想不到的時機呈現，不要提前預告，讓它自然發生

【寫作標準——每一條都是硬指標】
・開場第一段必須有鉤子，讀者看完想繼續讀
・主角的個人傷口要在前三分之一自然帶出——一個動作、一句話就夠
・反派要有動機，讓讀者理解但更恨他的選擇
・反轉必須有因果：反派怎麼輸，要和他怎麼作惡相對應
・具體 > 籠統：「這份合約價值2.3億」比「一大筆錢」強十倍
・每個場景必須同時推進劇情和角色，沒有廢筆
・對白要有性格：主角說話的方式要和反派截然不同

【三翻四抖節奏】
三次反轉（每次比上次更震撼）+ 四個高潮時刻（讀者忍不住截圖分享的那種）
裝逼是鋪墊，打臉是正題——主角越被低估，翻身時越讓人血脈賁張

【結局三步 — 必做，不得草率收場】
本篇結局方式：{unique['ending']}

無論用哪種結局方式，必須完成以下三步：
① 反派的下場要交代清楚（至少2-3句，說明他輸了什麼、失去什麼）
② 主角的最終狀態要有畫面感（用一個具體動作或場景定格）
③ 呼應開場埋下的細節或對白，讓故事首尾成環

結局最少佔全文 20%，禁止用一句話草草結束

【禁止清單】
✗ 「被羞辱→亮身份→眾人跪地」的流水線公式
✗ 開場超過150字才入正題
✗ 心理獨白多於對白和動作
✗ 反派莫名其妙變好人
✗ 結尾不足200字或用「從此過上幸福生活」一句帶過

字數：3000至4500字 ｜ 繁體中文 ｜ 直接從標題開始寫正文
{_trend}
開始："""


def _build_female_prompt(genre, character, villain, opening, winner_hint, unique, trending_hint=""):
    _trend = (
        f"\n【🔥 今日爆款素材參考（從實時熱搜蒸餾，自然融入 1-2 個最合適的，唔需要強塞）】\n{trending_hint}\n"
        if trending_hint else ""
    )
    return f"""你是頂尖中文網絡言情爽文作家，你的故事讓女性讀者看完想截圖轉發。

══════════════════════════════════
第一步：先在腦海中完成以下故事設計（不輸出這部分）
══════════════════════════════════

① 開場鉤子（第一句）
   必須是一句讓人無法停下的話，帶著撕裂感或懸念。
   好的鉤子範例：「離婚協議書送來的那天，她發現自己懷孕了——她沒有告訴任何人，只是把協議書簽了。」
   測試標準：看完第一句，讀者必須往下看。

② 「虐」的設計（讀者要先恨，才能後爽）
   反派如何當眾踐踏女主尊嚴？要夠具體，夠讓人心疼，讓讀者真的恨。
   虐得不夠真，後面的爽就沒力。

③ 諷刺結構設計（靈魂所在）
   反派的「原罪」和女主的「逆轉」如何形成完美諷刺？
   例：男主為白月光的「純潔」踐踏女主 → 白月光的醜陋被女主親手揭穿，而女主早已是白月光高攀不起的存在。
   本篇諷刺結構參考：{unique['irony']}

④ 女主逆轉設計
   她靠什麼贏？要夠具體，和情節有機結合，不能只是「亮出身份」。
   參考：{unique['trump_card']}

⑤ 反派動機設計（讓讀者理解但更恨他）
   {unique['villain_motivation']}
   → 反派不能只是壞，要讓讀者看懂他為何這樣做，然後更恨他選錯了方式

⑥ 懸念鉤子（讓讀者中段放不下）
   {unique['suspense_hook']}
   → 在故事前半結束前自然植入，不能提前解答，要讓讀者帶著這個疑問看完後半

⑦ 點睛之筆（令故事有靈魂）
   在開場埋一個細節，結尾時賦予它完全不同的意義。
   參考：{unique['memorable']}

⑧ 情感核心（讀者帶走什麼感受）
   {unique['emotional_core']}

⑨ 女主的個人傷口（讓讀者真正心疼的那一刻）
   {character['wound']}
   → 開場前三分之一自然埋入，一個動作或一句話就夠，不需要旁白解釋
   → 讓讀者說「我明白那種感覺」——這才是共鳴，不是悲慘

⑩ 本篇意外反轉種子（打破讀者預期的關鍵時刻）
   {unique['twist_seed']}
   → 在最意想不到的時機植入，讓讀者真的沒料到，不要提前預告

══════════════════════════════════
第二步：按以下設定寫正文
══════════════════════════════════

【本篇設定】
類型：{genre['name']} — {genre['desc']}
女主：{character['name']}（{character['gender']}／{character['occupation']}／{character['personality']}）
個人傷口：{character['wound']}
反派原型：{villain}
開場情境：{opening}
故事舞台：{unique['setting']}
敘事結構：{unique['structure']}{winner_hint}

{TITLE_RULE}

【本篇寫作風格 — 貫穿全文】
{unique['writing_style']}
→ 這是本篇的語感基調，從第一句到最後一句都要符合這個風格

{HOOK_DENSITY_RULE}

【反派動機——讓讀者理解但更恨她】
{unique['villain_motivation']}
→ 反派有動機，讀者越懂她的邏輯，越恨她選錯了路

【懸念鉤子——讓讀者中段放不下】
{unique['suspense_hook']}
→ 在故事前半結束前植入，不能提前解答

【意外反轉種子——打破讀者預期】
{unique['twist_seed']}
→ 不要提前預告，讓它自然發生，在最意想不到的時機

【女頻三幕結構——必須清晰】
第一幕「虐」：反派當眾踐踏女主，越具體越讓讀者心疼，要讓讀者真的恨
第二幕「轉」：女主決絕抽身，亮出底牌，全場震驚——轉折要出人意料，不能公式化
第三幕「爽」：反派追悔，女主雲淡風輕——女主的冷靜比反派的哭求更有力

【寫作標準——每一條都是硬指標】
・開場第一段必須帶撕裂感，讓讀者立刻心疼女主
・女主的個人傷口要在前三分之一自然帶出——一個細節、一個動作就夠，不要長篇說明
・反派要有動機，讓讀者理解但更恨她，不能只是純惡人
・反轉必須和「虐」的方式形成諷刺呼應，有因果感
・女主的強，要靠行動和對白體現，不靠旁白告訴讀者她很強
・具體 > 籠統：「她是顧氏旗下三家上市公司的實際掌舵人」比「她很厲害」強十倍

【結局三步 — 必做，不得草率收場】
本篇結局方式：{unique['ending']}

無論用哪種結局方式，必須完成以下三步：
① 反派／渣男的下場要交代清楚（至少2-3句，說明他們失去了什麼、求而不得什麼）
② 女主的最終狀態要有畫面感——她活得漂亮，用一個具體場景或動作定格她最好的樣子
③ 呼應開場埋下的細節或對白，讓故事首尾成環，一句金句讓讀者想轉發

結局最少佔全文 20%，禁止用一句話草草結束

【禁止清單】
✗ 「被羞辱→掏出身份→男主跪地求原諒」的流水線公式
✗ 女主在前三分之一就亮出底牌（虐得不夠深，爽就不夠）
✗ 長篇心理獨白代替行動和對白
✗ 反派莫名洗白，女主聖母大發慈悲原諒一切
✗ 結尾男主求復合，女主卻猶豫心軟（她已經贏了，不需要他了）
✗ 結尾不足200字或用「從此過上幸福生活」一句帶過

字數：3000至4500字 ｜ 繁體中文 ｜ 直接從標題開始寫正文
{_trend}
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

    # 若此類型有高分歷史，加入一條 DNA 參考提示
    winners = load_winners().get(genre["name"], [])
    winner_hint = ""
    if winners:
        ref = random.choice(winners)
        if "irony" in ref:
            # 新版 DNA 格式
            winner_hint = f"""
【⭐ 上次此類型獲最高評分的成功 DNA（參考結構，創作全新故事）】
諷刺結構：{ref.get('irony', '')}
主角王牌：{ref.get('trump_card', '')}
反派動機：{ref.get('villain_motivation', '')}
敘事結構：{ref.get('structure', '')}
寫作風格：{ref.get('writing_style', '')}
情感核心：{ref.get('emotional_core', '')}
反轉種子：{ref.get('twist_seed', '')}
結局方式：{ref.get('ending', '')}
→ 這套 DNA 組合曾讓讀者非常滿意，沿用相近的張力結構，但場景和人物必須全新"""
        else:
            # 舊版兼容
            winner_hint = f"""
【⭐ 上次此類型獲最高評分的成功設定（參考風格，創作全新故事）】
開場情境：{ref.get('opening', '')}
反派設定：{ref.get('villain', '')}
→ 此類開場和反派設計曾引發強烈爽感，可沿用相近的張力結構"""

    unique = _pick_unique_elements(genre.get("name", ""))

    # 抓實時 trending 素材（失敗唔影響主流程）
    trending_hint = ""
    try:
        from utils import fetch_trending_topics
        trending_hint = fetch_trending_topics(channel)
    except Exception as e:
        print(f"[generate_story] trending 抓取失敗（非致命）：{e}")

    if channel == "F":
        prompt = _build_female_prompt(genre, character, villain, opening, winner_hint, unique, trending_hint)
    else:
        prompt = _build_male_prompt(genre, character, villain, opening, winner_hint, unique, trending_hint)

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.1,
                max_tokens=7000,
            )
            return response.choices[0].message.content, villain, opening, unique
        except Exception as e:
            last_err = e
            print(f"[generate_story] 第 {attempt} 次失敗：{e}")
    raise RuntimeError(f"生成失敗（已重試 {max_retries} 次）：{last_err}")


def generate_and_send_one(genre_name=None, label="📖"):
    """按需生成並發送單篇故事。
    genre_name: 指定類型，None 則從高分類型中選。
    label: header 前綴，例如 '📖'（新生成）/ '📖 [加推]' / '📖 [指定]'。
    """
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
            # 高分類別中，再按追更率加權（留存高嘅更常出）
            genre = weighted_choice_retention(favored)
        elif recent:
            # 次選：最久未出現的類別（LRU），按 weight × 追更率加權
            recent_set = set(recent)
            unseen = [g for g in GENRES if g["name"] not in recent_set]
            genre = weighted_choice_retention(unseen) if unseen else weighted_choice_retention(GENRES)
        else:
            genre = weighted_choice_retention(GENRES)

    character = generate_character(genre.get("channel", "M"), genre.get("name", ""))
    _label_display = f" {label}" if label else ""
    send_telegram(f"✨ 生成中{_label_display}：{genre['name']} · {character['name']}，請稍候（約 30 秒）...")

    content, villain, opening, dna = generate_story(genre, character)
    print(f"[generate_and_send_one] 故事生成完成，字數={len(content)}")

    # 暫存 DNA 到 Redis，供評分時學習
    try:
        from utils import save_story_dna
        save_story_dna(genre["name"], dna)
    except Exception as e:
        print(f"[generate_and_send_one] save_story_dna 失敗（非致命）：{e}")

    # 存盤到今日故事檔案，供 /menu 重讀
    try:
        from utils import save_story_to_disk
        save_story_to_disk({
            "type": "novel",
            "genre": genre["name"],
            "channel": genre.get("channel", "M"),
            "character": character,
            "content": content,
        })
    except Exception as e:
        print(f"[generate_and_send_one] save_story_to_disk 失敗（非致命）：{e}")

    _header_label = f"  {label}" if label else ""
    _ch = genre.get("channel", "M")
    _ch_tag = "🔥 男頻" if _ch == "M" else "💕 女頻"
    header = (
        f"📖{_header_label}  {genre['name']}\n"
        f"👤 {character['name']} · {character['gender']} · {character['occupation']}  ｜  {_ch_tag}\n"
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


# ══════════════════════════════════════════════════════════════════
# ── Phase 1：連載追更引擎 ──────────────────────────────────────────
# 一個「系列」= 連續主角 + 世界觀 + 弧線(arc)，每集 800-1200 字收喺
# cliffhanger，Telegram「▶️ 下一集」即時解鎖。系列長度由 arc 決定(3-5 集)。
# ══════════════════════════════════════════════════════════════════

import re as _re
import uuid as _uuid

# 系列弧線骨架池（每個 beat = 一集，長度 3-5）
SERIES_ARCS = [
    {"name": "虐戀四幕", "channel": "F",
     "beats": ["當眾被虐、尊嚴被踐踏到底", "決絕轉身，亮出第一張底牌",
               "身份與真相層層揭開，全場震動", "終極反殺，對方跪地追悔莫及"]},
    {"name": "雙強五幕", "channel": "F",
     "beats": ["勢均力敵的初次交鋒", "彼此試探、暗中較勁", "危機逼近、被迫並肩",
               "最大反轉、關係翻盤", "雙向奔赴，各自封神"]},
    {"name": "重生復仇三幕", "channel": "F",
     "beats": ["重生歸來、看清前世死局", "步步算計、手撕渣男賤女", "奪回一切、活得肆意通透"]},
    {"name": "懸疑三幕", "channel": "F",
     "beats": ["迷局開場、拋出最大鉤子", "真相碎片、中段大反轉", "謎底爆發、情感與懸念同收"]},
    {"name": "逆襲五幕", "channel": "M",
     "beats": ["谷底受辱、萬人踩低", "暗中佈局初現端倪", "第一次當眾打臉",
               "反派反撲、危機升級", "全面碾壓、塵埃落定"]},
    {"name": "腦洞末世四幕", "channel": "M",
     "beats": ["末世降臨、規則崩壞", "覺醒異能、第一次逆襲", "陣營對決、人性考驗", "登頂終局、改寫規則"]},
    {"name": "馬甲三幕", "channel": "M",
     "beats": ["被當廢物、當眾看低", "第一層馬甲被踢爆、全場譁然", "頂級身份盡揭、震撼收場"]},
]


def _pick_arc(channel):
    pool = [a for a in SERIES_ARCS if a["channel"] == channel] or SERIES_ARCS
    return random.choice(pool)


def _build_episode_prompt(series, ep_num, unique, villain, trending_hint=""):
    """單集 prompt：只推進一個 beat，強制 cliffhanger + 控制碼。"""
    beats = series["arc"]
    beat = beats[ep_num - 1]
    total = len(beats)
    is_last = ep_num == total
    ch = series["channel"]
    c = series["character"]
    tone = ("女性讀者看完想截圖轉發的言情爽文" if ch == "F"
            else "讓人第一句就放不下的打臉逆襲爽文")
    if ep_num == 1:
        recap = ""
    else:
        _lc = series.get("last_choice", "")
        recap = f"\n【上集懸念（本集開場須接住並回應）】\n{series.get('next_hook', '')}\n"
        if _lc:
            recap += f"【讀者親自選擇了：「{_lc}」】本集必須順住呢個選擇發展，唔可以走返轉頭，要讓讀者覺得「係我嘅決定改寫咗劇情」。\n"

    if is_last:
        ending_rule = (
            "【本集為最終集】完整收束整個系列：\n"
            "① 反派下場交代清楚（失去什麼、求而不得什麼）\n"
            "② 主角最終狀態要有畫面感，用一個具體場景／動作定格\n"
            "③ 呼應第 1 集開場的細節或對白，首尾成環\n"
            "結尾另起一行輸出控制碼：<<<END>>>")
        title_rule = "唔好再寫標題，直接接住上集劇情。"
        word_rule = "1200-1800 字（終集可略長）｜完整結局最少佔本集 30%"
    else:
        ending_rule = (
            "【本集非最終集】必須收喺一個「逼讀者做決定」嘅 cliffhanger：主角行到關鍵岔口，\n"
            "兩條路都合理、都有代價。可以喺正文自然帶出呢個兩難。\n"
            "然後喺全文最尾，另起三行輸出控制碼，格式一字不差、每行都要用足三個尖括號：\n"
            "<<<NEXT: 一句下集懸念種子，20字內>>>\n"
            "<<<CA: 讀者選擇A，一個具體行動，12字內>>>\n"
            "<<<CB: 讀者選擇B，同A方向明顯不同，12字內>>>\n"
            "示範（照跟格式）：\n"
            "<<<NEXT: 律師信封裡的秘密即將曝光>>>\n<<<CA: 先私下調查律師>>>\n<<<CB: 即刻殺入會議室>>>")
        title_rule = ("首集：正文第一行寫一個爆款系列標題（獨立一行，用標題公式，"
                      "唔好加「第1集」字樣）。" if ep_num == 1
                      else "唔好再寫標題，直接接住上集劇情。")
        word_rule = "800-1200 字｜收尾必須吊人"

    _trend = (f"\n【今日爆款素材參考，自然融入 1 個最啱嘅】\n{trending_hint}\n"
              if trending_hint else "")

    return f"""你是頂尖中文網絡爽文作家，寫緊一個連載系列嘅「第 {ep_num}/{total} 集」，{tone}。

【系列設定（全系列一致，唔可改）】
類型：{series['genre']}
主角：{c['name']}（{c['gender']}／{c['occupation']}／{c['personality']}）
個人傷口：{c['wound']}
反派原型：{villain}
故事舞台：{unique['setting']}
寫作風格（全系列統一語感）：{unique['writing_style']}
{recap}
{TITLE_RULE if ep_num == 1 else ''}

【本集任務 — beat {ep_num}/{total}】
{beat}
→ 本集只推進呢一個 beat，唔好跳。節奏硬指標：每 200-300 字要有一個情緒點、
  資訊反轉或懸念，全程唔可以有悶場。

【標題規則】
{title_rule}

【結局／收尾規則】
{ending_rule}

【寫作硬指標】
・第一段即入戲，{('用開場鉤子撕裂感開篇' if ep_num == 1 else '接住上集張力')}
・具體 > 籠統（數字、頭銜、實物勝過形容詞）
・對白帶性格與潛台詞，主角同反派講嘢方式截然不同
・主角／女主嘅強靠行動同對白體現，唔靠旁白話讀者知

字數：{word_rule} ｜ 繁體中文 ｜ 直接開始寫：
{_trend}"""


def _parse_episode(raw):
    """抽出控制碼(NEXT/CA/CB/END)並從顯示文字清走。容錯：尖括號數目 1-3 都收。
    標題由呼叫方取正文第一行，唔靠控制碼（模型較穩定）。"""
    def _grab(tag):
        m = _re.search(r"<+\s*%s\s*[:：]\s*(.+?)>+" % tag, raw, _re.S)
        return m.group(1).strip() if m else None

    next_hook = _grab("NEXT")
    choice_a = _grab("CA")
    choice_b = _grab("CB")
    ended = bool(_re.search(r"<+\s*END\s*>+", raw))

    clean = _re.sub(r"<+\s*(?:TITLE|NEXT|CA|CB)\s*[:：].*?>+", "", raw, flags=_re.S)
    clean = _re.sub(r"<+\s*END\s*>+", "", clean)
    # 清走任何殘留半截控制碼行
    clean = _re.sub(r"^\s*<+\s*(?:TITLE|NEXT|CA|CB|END).*$", "", clean, flags=_re.M)
    # 清走殘留角括號（例如模型把標題包成 <<<標題>>>）
    clean = _re.sub(r"[<>]{2,}", "", clean)
    # 清走開頭殘留嘅「# 第N集」markdown 標題行（header 已顯示集數）
    clean = _re.sub(r"^\s*#{0,3}\s*第[0-9一二三四五六七八九十]+集\s*\n+", "", clean.lstrip())
    return clean.strip(), next_hook, choice_a, choice_b, ended


def start_new_series(genre_name=None):
    """開一個新連載系列並發送第 1 集。"""
    from utils import save_series
    genre = (next((g for g in GENRES if g["name"] == genre_name), None)
             if genre_name else weighted_choice(GENRES))
    if genre is None:
        genre = weighted_choice(GENRES)
    ch = genre.get("channel", "M")
    character = generate_character(ch, genre["name"])
    arc = _pick_arc(ch)
    unique = _pick_unique_elements(genre["name"])
    villain = random.choice(FEMALE_VILLAINS if ch == "F" else VILLAINS)
    series = {
        "id": "s" + _uuid.uuid4().hex[:5],
        "genre": genre["name"], "channel": ch,
        "character": character, "title": None,
        "arc": arc["beats"], "arc_name": arc["name"],
        "dna": unique, "villain": villain,
        "episodes": [], "next_hook": "", "status": "ongoing",
    }
    try:
        from utils import record_metric
        record_metric("start", genre["name"])
    except Exception:
        pass
    _generate_and_send_episode(series, 1)
    return series


def continue_series(series_id, choice_letter=None):
    """讀取指定系列並生成／發送下一集。choice_letter='a'/'b' 時按讀者選擇改寫方向。"""
    from utils import load_series
    series = load_series(series_id)
    if not series:
        send_telegram("⚠️ 搵唔到呢個系列（可能已過期），用 /series 開新一個。")
        return
    if series.get("status") == "completed":
        send_telegram("🎬 呢個系列已完結！開下一個？（/series）")
        return
    if choice_letter:
        pc = series.get("pending_choices", {})
        series["last_choice"] = pc.get(choice_letter, "")
    try:
        from utils import record_metric
        record_metric("continue", series["genre"])
        if choice_letter:
            record_metric("choice", series["genre"])
    except Exception:
        pass
    _generate_and_send_episode(series, len(series.get("episodes", [])) + 1)
    return series


def _generate_and_send_episode(series, ep_num):
    """生成單集、存 Redis、連按鈕發送。"""
    from utils import save_series
    ch = series["channel"]
    total = len(series["arc"])
    _title_disp = series.get("title") or series["genre"]
    send_telegram(f"✨ 生成中：《{_title_disp}》第 {ep_num}/{total} 集，請稍候（約 30 秒）...")

    trending_hint = ""
    try:
        from utils import fetch_trending_topics
        trending_hint = fetch_trending_topics(ch)
    except Exception as e:
        print(f"[episode] trending 抓取失敗（非致命）：{e}")

    prompt = _build_episode_prompt(series, ep_num, series["dna"], series["villain"], trending_hint)
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    raw = None
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.1,
                max_tokens=4000,
            )
            raw = resp.choices[0].message.content
            break
        except Exception as e:
            last_err = e
            print(f"[episode] 第 {attempt} 次失敗：{e}")
    if raw is None:
        raise RuntimeError(f"單集生成失敗（已重試 3 次）：{last_err}")

    clean, next_hook, choice_a, choice_b, ended = _parse_episode(raw)
    if ep_num == 1 and not series.get("title"):
        # 取正文第一行做系列標題
        for line in clean.split("\n"):
            if line.strip():
                series["title"] = line.strip()
                break
    series.setdefault("episodes", []).append({"ep": ep_num, "content": clean})
    if next_hook:
        series["next_hook"] = next_hook
    series["pending_choices"] = ({"a": choice_a, "b": choice_b}
                                 if (choice_a and choice_b) else {})
    if ended or ep_num >= total:
        series["status"] = "completed"
    save_series(series)
    if series["status"] == "completed":
        try:
            from utils import record_metric
            record_metric("complete", series["genre"])
        except Exception:
            pass
    print(f"[episode] 系列 {series['id']} 第 {ep_num}/{total} 集完成，status={series['status']}，字數={len(clean)}")

    is_done = series["status"] == "completed"
    ch_tag = "💕 女頻" if ch == "F" else "🔥 男頻"
    _title_disp = series.get("title") or series["genre"]
    header = (
        f"📖 《{_title_disp}》 第 {ep_num}/{total} 集\n"
        f"👤 {series['character']['name']} ｜ {ch_tag} ｜ {series['arc_name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    _gn = series["genre"]
    # 「換過個」出口：睇完唔啱可以即刻轉新故事（唔追本身就係負評訊號，留存數據會扣低此題材）
    _switch_btn = {"text": "🎲 換個新故事", "callback_data": "newseries"}
    _fav_btn = {"text": "⭐ 收藏", "callback_data": f"favx_{_gn}"}
    if is_done:
        # 終集：彈返評分，評整個系列（餵 winner 學習 + 互動率）
        footer = "\n\n━━━━━━━━━━\n🎬 本系列完結，覺得點？"
        kb = {"inline_keyboard": [
            [{"text": "😞 差",   "callback_data": f"ratex_1_{_gn}"},
             {"text": "😐 一般", "callback_data": f"ratex_2_{_gn}"},
             {"text": "😊 好",   "callback_data": f"ratex_3_{_gn}"},
             {"text": "🤩 超好", "callback_data": f"ratex_4_{_gn}"}],
            [{"text": "🎬 開新系列", "callback_data": "newseries"}, _fav_btn],
        ]}
    else:
        pc = series.get("pending_choices", {})
        ca, cb = pc.get("a"), pc.get("b")
        if ca and cb:
            footer = f"\n\n━━━━━━━━━━\n👇 你想點？你嘅選擇改寫下一集（{ep_num}/{total}）"
            kb = {"inline_keyboard": [
                [{"text": f"🔥 {ca}", "callback_data": f"choose_{series['id']}_a"}],
                [{"text": f"❄️ {cb}", "callback_data": f"choose_{series['id']}_b"}],
                [_switch_btn, _fav_btn],
            ]}
        else:
            # fallback：若模型冇出選擇，退回單純「下一集」
            footer = f"\n\n━━━━━━━━━━\n👇 追落去（{ep_num}/{total}）"
            kb = {"inline_keyboard": [
                [{"text": f"▶️ 下一集（{ep_num + 1}/{total}）", "callback_data": f"nextep_{series['id']}"}],
                [_switch_btn, _fav_btn],
            ]}
    send_telegram(header + clean + footer, reply_markup=kb)
    print(f"[episode] send_telegram 完成 {series['id']} ep{ep_num}")


