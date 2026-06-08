# 每日小說生成器

每隔一日早上 9am 自動生成 3 篇中文網絡爽文，推送到 Telegram。支援評分回饋、加權類別選取、按需即時生成。

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

- **隔日生成**：每逢單數日（1/3/5...）早上 9am 自動跑
- **3 篇故事**：從 21 個類別加權抽 3 個，各配隨機主角
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

## 故事類別池（21 個）

重生逆襲、打臉爽文、職場逆襲、馬甲文、系統流、醫術流、商戰逆襲、豪門真假身份、都市隱世強者、穿越古代稱霸、鑑寶奇才、贅婿稱王、學霸裝弱、末世崛起、復仇歸來、甜寵逆襲、古言權謀、競技熱血、玄學風水、神豪撒幣、前任悔恨記

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

**Cron Job**（生成腳本）
```
0 9 */2 * *  python3 /Users/stephanieau/daily-novel/novel_generator.py >> /Users/stephanieau/daily-novel/cron.log 2>&1
```

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
