# 每日小說生成器

按需生成中文網絡爽文，推送到 Telegram（已取消自動排程）。支援評分回饋、加權類別選取、即時生成。

## 架構

```
daily-novel/
├── novel_generator.py   # 主腳本：生成故事並發送（支援平行生成）
├── bot_listener.py      # 後台服務：處理 Telegram 按鈕 & 指令互動
├── utils.py             # 共用工具：genre data I/O、Telegram 發送、目錄選單
├── .env                 # API Keys（已加入 .gitignore，勿 commit）
├── .gitignore           # 排除 .env、stories/、genre_data.json、日誌
├── requirements.txt
├── cron.log             # 生成日誌
├── bot_listener.log     # Bot 日誌
└── stories/             # 每次生成的故事存檔（YYYY-MM-DD.json）
```

## 功能

- **按需生成**：自己選擇時間執行 `python3 novel_generator.py` 或 Telegram `/now`
- **3 篇故事**：從 25 個類別（男頻/女頻加權）抽 3 個，各配隨機主角
- **平行生成**：3 篇同時呼叫 DeepSeek API，總時間壓縮到約 1 篇的等待
- **主角隨機**：從大型姓名池組合，避免 AI 重複生成相似名字
- **Telegram 推送**：每篇獨立訊息 + 結尾目錄 + 底部快捷鍵盤
- **底部快捷鍵盤**：`[📖 故事1] [📖 故事2] [📖 故事3]` 常駐，一 tap 重讀
- **`/menu` 指令**：顯示今日類別 + 主角名的可點擊目錄
- **評分系統**：每篇結尾有 4 級評分按鈕，高分類別自動提升出現頻率
- **加推功能**：評 🤩 超好後詢問是否即時加推同類型故事
- **Retry 機制**：DeepSeek API 及 Telegram 發送失敗自動重試最多 3 次
- **Log rotation**：`bot_listener.log` 最大 5MB，自動保留最近 3 份，唔會無限增長
- **`/history` 指令**：瀏覽最近 7 日故事，tap 日期即可重讀當日目錄
- **自動清理**：每次生成後自動刪除 30 日前的故事存檔
- **智慧 `/more`**：有評分則選高分類別；無評分則選最久未出現的類別（LRU），唔再純隨機

## 故事類別池（25 個，男頻/女頻加權）

- **男頻（15，weight 1）**：重生逆襲、打臉爽文、職場逆襲、馬甲文、系統流、商戰逆襲、豪門真假身份、都市隱世強者、穿越古代稱霸、贅婿稱王、學霸裝弱、復仇歸來、甜寵逆襲、玄學風水、前任悔恨記
- **女頻（10，weight 2）**：追妻火葬場、替嫁先婚後愛、重生虐戀復仇、總裁甜寵、雙重生、馬甲千金、死遁離婚、穿書反派、團寵真千金、古言寵妃

## Bot 指令

| 指令 | 說明 |
|------|------|
| `/now` | 即時生成 1 篇新故事 |
| `/list` | 瀏覽所有類別，tap 即生成 |
| `/more` | 從高分類別加推 1 篇 |
| `/stats` | 查看各類別評分統計 |
| `/menu` | 重讀今日故事目錄 |
| `/history` | 瀏覽最近 7 日故事 |
| `/help` | 指令說明 |

## 費用估算

| 項目 | 數量 |
|------|------|
| 每次生成 tokens | ~31,000 |
| 每月生成次數 | ~15 次 |
| 月費 | ~HK$4 |

使用 DeepSeek-V3（deepseek-chat）。

## 自動化設置

已取消自動 cron 生成，改為按需執行 `python3 novel_generator.py` 或 Telegram `/now`。

**LaunchAgent**（Bot 常駐服務）
```
~/Library/LaunchAgents/com.stephanieau.novel-bot.plist
```
開機自動啟動，crash 自動重啟。

## 常用指令

```bash
# 立即測試生成
python3 /Users/stephanieau/daily-novel/novel_generator.py

# 查看生成日誌
tail -f /Users/stephanieau/daily-novel/cron.log

# 查看 Bot 日誌
tail -f /Users/stephanieau/daily-novel/bot_listener.log

# 重啟 Bot
launchctl stop com.stephanieau.novel-bot
launchctl start com.stephanieau.novel-bot
```

## 環境變數（.env）

```
DEEPSEEK_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

## 安裝依賴

```bash
pip install -r requirements.txt
```
