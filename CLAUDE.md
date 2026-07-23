# CLAUDE.md — novel-web（網站小說產品）

Repo 核心 = 網站產品 **novel-web**（Next.js + Supabase）：故事牆 + 登入 + 個人化結局。舊 Telegram 小說 bot 已於 **2026-07-11 移除**（檔案已從 repo 刪走，翻查舊邏輯睇 git 歷史 commit），正式 deprecated。

> 內容系統詳解拆咗落 `docs/SYSTEMS.md`，按需 read_file。

## ⚙️ Standards（MANDATORY — 正本：`stephanie-personal/docs/ai-governance/06-STANDARDS.md`，改規則只改正本）

Push（`github_push.py` 永不 git CLI・HTTPS・一次 run 一 commit）・寫入分流（改動記錄 → `CHANGELOG.md` **頂部**，唔准 append 落本檔；本檔上限 100 行/6KB）・清理 mv `_to_delete/`・改舊檔先 `.bak-YYYYMMDD`・方向性決定先 preview・改完以用家身份 run 一次先報完成・governance 00–05（派 subagent 先讀 01+03；報完成前過 02 §R2；冇 mount stephanie-personal → 叫 Stephanie 連埋）。詳文＋例外表 → 正本。


## 產品出口 = novel-web

**novel-web**（獨立 repo `github.com/auzistephanie/novel-web`，唔屬於呢個 repo 嘅 git 版本控制，`.gitignore` 已排除。本機位置仍係 `daily-novel/novel-web/`，未搬去獨立 `~/novel-web/`——搬機重組暫緩，搬咗先改）：Next.js + Supabase login + 故事牆 + 個人化結局，由 Cowork scheduled task（`novel-story-generator` 12:30/16:30）直接用 Claude 生成內容寫入 Supabase（結局改由讀者主動揀分支即時生成，`novel-ending-generator` task 已於 2026-07-10 刪除，詳見 `novel-web/CLAUDE.md`）。新功能／新故事出口去 novel-web 自己嘅 `CLAUDE.md`。

## 舊 Telegram bot（2026-07-11 已移除）

`novel_generator.py`／`lit_generator.py`／`bot_listener.py`／`utils.py`／`webhook_server.py`／`check_errors.py`／`sync_commands.py` 等已從 repo 刪走（唔再存在磁碟；翻查舊邏輯睇 git 歷史 commit）。LaunchAgent `com.stephanieau.novel-bot` 應 `launchctl unload` + 刪 plist。

## 推送本 repo

> 正本 → ⚙️ Standards §S1。本 repo：root `github_push.py`。novel-web 有自己嘅 `github_push.py`（PAT 喺 `novel-web/.env`；`push-novel-web.sh`／plain git CLI 已停用）；⚠️ 雲端 sandbox 對 novel-web 跑 API push 會撞 403（session 未 allowlist）→ `device_commit_files` 交返本機跑，詳見 `novel-web/CLAUDE.md`「開發須知」。

## ✅ 完成前檢查（本 repo 專屬 DoD；通用四格 → 02-JUDGMENT §R2）

1. 改 novel-web 相關 → 跟 `novel-web/CLAUDE.md` 嘅驗法實際行一次（嗰邊有自己規則）
2. 改本 repo script（root／`scripts/`／`shortdrama/`／`videoclip/`）→ 實跑一次貼 output
3. Push：root `python3 github_push.py "<msg>"`（novel-web 改動用佢自己嗰份）＋核實 GitHub HEAD（→ Standards §S1）

## 📖 文件讀取規則

| 需要嘅資訊 | 讀邊份 |
|---|---|
| 產品：故事牆 / 結局 / Supabase | `novel-web/CLAUDE.md` |
| 短劇 video pipeline（storyboard／fal.ai／併片，收費真·圖生片） | `shortdrama/CLAUDE.md` |
| 免費短片 pipeline（AI圖＋Ken Burns運鏡＋EdgeTTS旁白） | `videoclip/CLAUDE.md` |
| 歷史：類別系統、分頻、連載、留存數據 | `docs/SYSTEMS.md`（bot 年代參考）|
| 改版歷史 | `CHANGELOG.md` |
| AI 調度/驗證/判斷制度（全 repo 共用） | `stephanie-personal/docs/ai-governance/` |

（AI 制度＋push＋分流規則 → 見頂部 ⚙️ Standards block）
