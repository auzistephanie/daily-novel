# CLAUDE.md — 每日小說生成器

按需生成中文網絡爽文（自己選擇時間先生成，唔再自動排程），推送 Telegram。DeepSeek-V3 生成，支援評分回饋、加權選類、即時生成。

## 核心檔案
- `novel_generator.py` — 主腳本：類別池、主角生成、故事生成、加推
- `bot_listener.py` — Telegram 後台服務（按鈕 / 指令互動）
- `utils.py` — genre data I/O、Telegram 發送
- `genre_data.json` — 評分與 winners 記憶（本地，唔 commit）
- `.env` — API keys（含 GITHUB_TOKEN，唔 commit）
- `github_push.py` — 用 GitHub API push（PAT in .env），完成重大更新後自動執行：`python3 github_push.py "<commit message>"`

## 類別系統（2026-07 最新版）

25 個類別，每個有 `channel`（M 男頻 / F 女頻）+ `weight`（加權）。

- **男頻（14，weight 1-2）**：重生逆襲、打臉爽文、職場逆襲、馬甲文、系統流、商戰逆襲、豪門真假身份、都市隱世強者、穿越古代稱霸、贅婿稱王、學霸裝弱、復仇歸來、前任悔恨記、漫畫感爽文（w2）
- **女頻（11，weight 2 = 2025-26 市場爆款，加重出現）**：追妻火葬場、替嫁先婚後愛、重生虐戀復仇、總裁甜寵、雙重生、馬甲千金、死遁離婚、穿書反派、團寵真千金、古言寵妃、懸疑言情

抽選用 `weighted_choice()`，女頻佔比約 58%。`generate_character(channel)` 會按頻道配主角性別／身份／性格池。

## 分頻寫法（generate_story）

按 genre `channel` 揀模板：
- **男頻** `_build_male_prompt`：三翻四抖打臉，實力碾壓
- **女頻** `_build_female_prompt`：虐渣 + 追悔 + 雙向反轉，情緒張力 > 邏輯碾壓

兩者共用 `TITLE_RULE`（爆款標題公式）：`[身份／情境鉤子]，[反轉／衝突結果]`，每篇先構思 3 個候選標題揀最強。

女頻專屬池：`FEMALE_VILLAINS`、`FEMALE_OCCUPATIONS`、`FEMALE_PERSONALITIES`、`FEMALE_OPENING_HOOKS`。

## Bot 指令
`/now` 即時生成 · `/list` 瀏覽類別 · `/more` 高分加推 · `/stats` 評分統計 · `/menu` 今日目錄 · `/history` 近 7 日 · `/help`

## 自動化
- 已取消自動 cron 生成，改為按需執行 `python3 novel_generator.py` 或 Telegram `/now`
- LaunchAgent：`com.stephanieau.novel-bot.plist`（Bot 常駐，crash 自動重啟）

## 改版歷史
- **2026-06-11**：取消每隔一日 9am 自動生成 cron，改為自己選擇時間按需生成
- **2026-06-11**：刪 6 個男頻冷門類別（醫術流／古言權謀／鑑寶奇才／神豪撒幣／末世崛起／競技熱血）；新增 10 個女頻言情爆款 + channel/weight 加權系統；加爆款標題公式；男女頻分開 prompt 模板。
- **2026-06-23**：刪甜寵逆襲（男頻，市場飽和）、玄學風水（冷門）；新增漫畫感爽文（M, w2）、重生年代稱霸（M, w2）、懸疑言情（F, w2）——對應 2026 短劇爆款趨勢。
- **2026-07-01**：刪重生年代稱霸（風格特殊，整合難度高）；/now 同 /lit 合併為隨機生成；加 CHARACTER_WOUNDS、TWIST_SEEDS、VILLAIN_MOTIVATIONS、SUSPENSE_HOOKS 池提升故事質量。
