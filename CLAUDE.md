# CLAUDE.md — 每日小說生成器

按需生成中文網絡爽文（自己揀時間生成，唔自動排程），推送 Telegram。DeepSeek-V3 生成，支援評分回饋、加權選類、連載追更 + 讀者選擇分支。

> 內容系統詳解拆咗落 `docs/SYSTEMS.md`，按需 read_file。

## ⚠️ 2026-07-04 起：唔再以 Telegram 為主要出口

新方向係網站產品 **novel-web**（獨立 repo `github.com/auzistephanie/novel-web`，唔屬於呢個 repo 嘅 git 版本控制，`.gitignore` 已排除。本機位置：公司機（舊）= `daily-novel/novel-web/`；自己機（2026-07-05 搬機重組後）= 獨立 top-level folder `~/novel-web/`）：Next.js + Supabase login + 故事牆 + 個人化結局，由 Cowork scheduled task（`novel-story-generator` 12:30/16:30 / `novel-ending-generator` 17:05；2026-07-05 錯開撞鐘＋加 heartbeat 落 watchdog）直接用 Claude 生成內容寫入 Supabase，唔再經呢度嘅 `novel_generator.py` / DeepSeek API / Telegram bot。

依家呢個 repo（`novel_generator.py`、`bot_listener.py`、Telegram 指令）**未刪**，Stephanie 未話幾時停 bot，但新功能／新故事出口請去 novel-web repo 嘅 `CLAUDE.md` 睇（位置見上）。

## 📖 文件讀取規則

| 需要嘅資訊 | 讀邊份 |
|---|---|
| 類別系統（28類/加權）、分頻寫法、連載追更（arcs/callbacks/Redis keys）、留存數據系統 | `docs/SYSTEMS.md` |
| 改版歷史 | `CHANGELOG.md`（唔需要每次讀）|
| AI 調度/驗證/判斷制度（全 repo 共用） | `stephanie-personal/docs/ai-governance/`（見下）|

## 核心檔案

- `novel_generator.py` — 主腳本：類別池、主角生成、故事生成、加推、連載（`SERIES_ARCS`、`start_new_series` 等）
- `bot_listener.py` — Telegram 後台服務（按鈕 / 指令互動）
- `utils.py` — genre data I/O、Telegram 發送、series/metrics Redis I/O
- `genre_data.json` — 評分與 winners 記憶（本地，唔 commit）· `.env` — API keys（唔 commit）
- `github_push.py` — GitHub API push（PAT in .env），重大更新後自動執行：`python3 github_push.py "<commit message>"`
- `sync_commands.py` — 同步 Telegram「/」指令 menu（setMyCommands），**改完指令後即刻跑，毋須重啟 bot**：`python3 sync_commands.py`。注意：menu 顯示同指令處理係兩件事——新指令要真正有反應仍要重啟 bot 載新 code

## Bot 指令

`/series` 連載（開新／續集）· `/now` 即時單篇 · `/browse` 揀類別 · `/more` 高分加推 · `/stats` 評分＋留存面板 · `/library` · `/history` 近 7 日 · `/help`

## 自動化

- 已取消自動 cron 生成，按需執行 `python3 novel_generator.py` 或 Telegram `/now`
- LaunchAgent：`com.stephanieau.novel-bot.plist`（Bot 常駐，crash 自動重啟）

## AI 制度（全 repo 共用正本）

正本：`stephanie-personal/docs/ai-governance/`（00 診斷 · 01 調度守則 · 02 判斷 rubric · 03 派工模板 · 04 維護協議 · 05 給未來 session 的信）。
決定咗要派 subagent（門檻見 01 §1，唔係乜都派）先讀 01+03；報「完成」前過一次 02 §R2。
⚠️ Session 冇 mount stephanie-personal folder → 叫 Stephanie 連埋佢，唔好靜靜地跳過成套制度。
