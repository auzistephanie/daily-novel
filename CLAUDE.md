# CLAUDE.md — novel-web（網站小說產品）

Repo 核心 = 網站產品 **novel-web**（Next.js + Supabase）：故事牆 + 登入 + 個人化結局。舊 Telegram 小說 bot 已於 **2026-07-11 移除**（檔案已從 repo 刪走，翻查舊邏輯睇 git 歷史 commit），正式 deprecated。

> 內容系統詳解拆咗落 `docs/SYSTEMS.md`，按需 read_file。

## ✍️ 寫入分流（MANDATORY — 想更新本檔前先讀）

- **改動記錄／開發史** → root `CHANGELOG.md` **頂部**，唔准 append 落本檔；本檔硬上限 **100 行／6KB**
- 本檔只准改：路由行、現行規則本身變咗。完整分流表 → `stephanie-personal/docs/ai-governance/04-MAINTENANCE.md` §0


## 產品出口 = novel-web

**novel-web**（獨立 repo `github.com/auzistephanie/novel-web`，唔屬於呢個 repo 嘅 git 版本控制，`.gitignore` 已排除。本機位置仍係 `daily-novel/novel-web/`，未搬去獨立 `~/novel-web/`——搬機重組暫緩，搬咗先改）：Next.js + Supabase login + 故事牆 + 個人化結局，由 Cowork scheduled task（`novel-story-generator` 12:30/16:30）直接用 Claude 生成內容寫入 Supabase（結局改由讀者主動揀分支即時生成，`novel-ending-generator` task 已於 2026-07-10 刪除，詳見 `novel-web/CLAUDE.md`）。新功能／新故事出口去 novel-web 自己嘅 `CLAUDE.md`。

## 舊 Telegram bot（2026-07-11 已移除）

`novel_generator.py`／`lit_generator.py`／`bot_listener.py`／`utils.py`／`webhook_server.py`／`check_errors.py`／`sync_commands.py` 等已從 repo 刪走（唔再存在磁碟；翻查舊邏輯睇 git 歷史 commit）。LaunchAgent `com.stephanieau.novel-bot` 應 `launchctl unload` + 刪 plist。

## 推送本 repo

`python3 github_push.py "<commit message>"`（GitHub API push，PAT in `.env`；已尊重 `.gitignore`，`_to_delete/` 唔會上）。novel-web 有自己嘅 `push-novel-web.sh` 獨立部署。

## 📖 文件讀取規則

| 需要嘅資訊 | 讀邊份 |
|---|---|
| 產品：故事牆 / 結局 / Supabase | `novel-web/CLAUDE.md` |
| 歷史：類別系統、分頻、連載、留存數據 | `docs/SYSTEMS.md`（bot 年代參考）|
| 改版歷史 | `CHANGELOG.md` |
| AI 調度/驗證/判斷制度（全 repo 共用） | `stephanie-personal/docs/ai-governance/` |

## AI 制度（全 repo 共用正本）

正本：`stephanie-personal/docs/ai-governance/`（00 診斷 · 01 調度守則 · 02 判斷 rubric · 03 派工模板 · 04 維護協議 · 05 給未來 session 的信）。
決定咗要派 subagent（門檻見 01 §1，唔係乜都派）先讀 01+03；報「完成」前過一次 02 §R2。
⚠️ Session 冇 mount stephanie-personal folder（REQUIRED core folder，唔係 optional）→ 叫 Stephanie 連埋佢，唔好靜靜地跳過成套制度。
