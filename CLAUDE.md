# CLAUDE.md — 每日小說生成器

按需生成中文網絡爽文（自己選擇時間先生成，唔再自動排程），推送 Telegram。DeepSeek-V3 生成，支援評分回饋、加權選類、即時生成、**連載追更 + 讀者選擇分支**。

## 核心檔案
- `novel_generator.py` — 主腳本：類別池、主角生成、故事生成、加推
- `bot_listener.py` — Telegram 後台服務（按鈕 / 指令互動）
- `utils.py` — genre data I/O、Telegram 發送
- `genre_data.json` — 評分與 winners 記憶（本地，唔 commit）
- `.env` — API keys（含 GITHUB_TOKEN，唔 commit）
- `github_push.py` — 用 GitHub API push（PAT in .env），完成重大更新後自動執行：`python3 github_push.py "<commit message>"`
- `sync_commands.py` — 同步 Telegram「/」指令 menu（setMyCommands），**改完指令後即刻跑，毋須重啟 bot**：`python3 sync_commands.py`。menu 顯示同指令處理係兩件事：menu 靠 setMyCommands（可獨立同步），新指令要真正有反應則仍要重啟 bot 載新 code。

## 類別系統（2026-07 最新版）

28 個類別，每個有 `channel`（M 男頻 / F 女頻）+ `weight`（加權）。

- **男頻（16，weight 1-2）**：重生逆襲、打臉爽文、職場逆襲、馬甲文、系統流、商戰逆襲、豪門真假身份、都市隱世強者、穿越古代稱霸、贅婿稱王、學霸裝弱、復仇歸來、前任悔恨記、漫畫感爽文（w2）、**末世腦洞（w2）**、**都市情緒流（w2）**
- **女頻（12，weight 2 = 2025-26 市場爆款，加重出現）**：追妻火葬場、替嫁先婚後愛、重生虐戀復仇、總裁甜寵、雙重生、馬甲千金、死遁離婚、穿書反派、團寵真千金、古言寵妃、懸疑言情、**雙強對峙**

> **2026-07-02 Phase 2**：新增末世腦洞／都市情緒流（男頻 2026 腦洞末世＋都市情緒爆點）、雙強對峙（女頻由單強虐渣轉「雙強」）。

抽選用 `weighted_choice()`，女頻佔比約 55%。`generate_character(channel)` 會按頻道配主角性別／身份／性格池。

## 分頻寫法（generate_story）

按 genre `channel` 揀模板：
- **男頻** `_build_male_prompt`：三翻四抖打臉，實力碾壓
- **女頻** `_build_female_prompt`：虐渣 + 追悔 + 雙向反轉，情緒張力 > 邏輯碾壓

兩者共用 `TITLE_RULE`（爆款標題公式）：`[身份／情境鉤子]，[反轉／衝突結果]`，每篇先構思 3 個候選標題揀最強。亦共用 `HOOK_DENSITY_RULE`（Phase 2 短劇節奏）：每 200-300 字要有一個鉤（情緒點／小反轉／新資訊／懸念），杜絕悶場。

女頻專屬池：`FEMALE_VILLAINS`、`FEMALE_OCCUPATIONS`、`FEMALE_PERSONALITIES`、`FEMALE_OPENING_HOOKS`。

## 連載追更系統（2026-07 Phase 1｜追睇引擎）

單篇一次過完結唔夠「追」。連載系統令一個故事 = 連續主角 + 世界觀 + 弧線(arc)，每集 800-1200 字收喺 cliffhanger，逼讀者追落去。核心設計兩條腿：

- **A 需求驅動**：唔係全部連載。單篇照出做「發現」，讀者畀「🤩 超好」評分時，先彈「📖 續寫成連載」按鈕（callback `serialize_{genre}`）。只連載已證爆款，零浪費 API。`/series` 亦可手動開新／續集。
- **出口 + 評分**：每集加「🎲 換個新故事」（callback `newseries`）——睇完唔啱即刻轉，唔追本身就係最強負評訊號（留存數據自動扣低此題材）。終集完結彈返 😞😐😊🤩 評分整個系列（`ratex_{score}_{genre}`），餵 winner 學習＋互動率。
- **B 讀者選擇分支**：每集尾模型輸出 `<<<CA>>>`/`<<<CB>>>` 兩個選擇 → 化成按鈕（callback `choose_{sid}_{a|b}`）。讀者一撳，`last_choice` 寫入系列，下集按嗰個方向寫——讀者變共同作者。

實作（`novel_generator.py`）：`SERIES_ARCS`（7 條弧線，長度 3-5，每 beat = 一集，含男頻末世腦洞／女頻雙強等 2026 爆點）、`start_new_series()`、`continue_series(id, choice)`、`_generate_and_send_episode()`、`_build_episode_prompt()`（單集 prompt + 強制岔口 cliffhanger）、`_parse_episode()`（容錯抽 NEXT/CA/CB/END，標題取正文第一行）。系列狀態存 Redis：`utils.save_series/load_series/list_ongoing_series`（key `series:{id}` TTL 30 日 + `series:ongoing` 索引）。

## 留存數據系統（2026-07 Phase 3｜追更率驅動）

Telegram bot 冇「已讀」回執，量度唔到開篇率；改為追蹤收到嘅**點擊事件**：`start`（開新系列）／`continue`（撳下一集/選擇掣）／`choice`（用選擇分支）／`complete`（追到終集）。存 Redis key `retention_metrics`（`{genre:{start,continue,choice,complete}}`）。

實作：`utils.record_metric/load_metrics/save_metrics`；埋點喺 `start_new_series`（start）、`continue_series`（continue/choice）、`_generate_and_send_episode`（complete）。**追更率驅動選類**：`_retention_multiplier()`（完讀率＋平均追更集數 → 0.5-3.0 倍）＋ `weighted_choice_retention()`，令 `generate_and_send_one` 選類由「評分驅動」升級「追更率驅動」——黐人題材自動更常出。`/stats` 加留存面板（各題材追更率／完讀率／分支互動）。

## Bot 指令
`/series` 連載追更（開新／續集）· `/now` 即時生成單篇 · `/browse` 揀類別 · `/more` 高分加推 · `/stats` 評分統計＋留存面板 · `/library` 故事庫 · `/history` 近 7 日 · `/help`

## 自動化
- 已取消自動 cron 生成，改為按需執行 `python3 novel_generator.py` 或 Telegram `/now`
- LaunchAgent：`com.stephanieau.novel-bot.plist`（Bot 常駐，crash 自動重啟）

## 改版歷史
- **2026-06-11**：取消每隔一日 9am 自動生成 cron，改為自己選擇時間按需生成
- **2026-06-11**：刪 6 個男頻冷門類別（醫術流／古言權謀／鑑寶奇才／神豪撒幣／末世崛起／競技熱血）；新增 10 個女頻言情爆款 + channel/weight 加權系統；加爆款標題公式；男女頻分開 prompt 模板。
- **2026-06-23**：刪甜寵逆襲（男頻，市場飽和）、玄學風水（冷門）；新增漫畫感爽文（M, w2）、重生年代稱霸（M, w2）、懸疑言情（F, w2）——對應 2026 短劇爆款趨勢。
- **2026-07-01**：刪重生年代稱霸（風格特殊，整合難度高）；/now 同 /lit 合併為隨機生成；加 CHARACTER_WOUNDS、TWIST_SEEDS、VILLAIN_MOTIVATIONS、SUSPENSE_HOOKS 池提升故事質量。
- **2026-07-02**：**Phase 1 追睇引擎**——由「短篇機」變「追劇機」。新增連載系統（`SERIES_ARCS` 7 條弧線 3-5 集，每集收 cliffhanger）+ 需求驅動（🤩 超好 → 續寫成連載）+ 讀者選擇分支（每集尾 2 選擇改寫下集）。新指令 `/series`。已用家身份實跑驗證：ep1 標題+選擇掣、ep2 接住讀者選擇、ep3 終集完結，劇情連貫、無殘留控制碼。對應 2026 短劇「密集反轉 + 追更留存」趨勢。
- **2026-07-02**：**Phase 2 題材+節奏**——GENRES 加末世腦洞(M,w2)／都市情緒流(M,w2)／雙強對峙(F,w2)（對應 2026 男頻腦洞末世＋都市情緒、女頻雙強爆點），共 28 類。新增 `HOOK_DENSITY_RULE` 注入單篇男女 prompt，令單篇都有短劇密集節奏。
- **2026-07-02**：**Phase 3 留存數據**——追蹤 start/continue/choice/complete 點擊事件（Redis `retention_metrics`），選類由評分驅動升級「追更率驅動」（`_retention_multiplier`＋`weighted_choice_retention`），`/stats` 加追更率／完讀率／互動率面板。離線驗證：埋點正確、黐人題材倍數 1.68、抽樣被選 3.2 倍。另加 `sync_commands.py` 解決改指令後 Telegram menu 唔更新（setMyCommands 獨立同步、毋須重啟 bot）。
