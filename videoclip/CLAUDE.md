# CLAUDE.md — videoclip（免費短片 pipeline）

由 daily-novel/novel-web 現有文字故事庫（Supabase `novel_stories`）做劇本源頭，轉做**全免費**短片（旁白＋AI 圖＋Ken Burns 運鏡）嘅子系統。2026-07-23 開設，同 `shortdrama/`（fal.ai 收費短劇）平行——videoclip 係零成本版，shortdrama 係課金真·圖生片版。獨立 subfolder，跟 daily-novel repo 一齊 push。

## 同 shortdrama 分別

| | videoclip（呢個） | shortdrama |
|---|---|---|
| 畫面 | AI **靜態圖** + ffmpeg 運鏡（攝影機郁，畫面內容唔郁） | fal.ai 逐鏡**生片**（畫面內容真·郁） |
| 成本 | 全免費 | ~US$2.4/集起 |
| 用途 | 日更試水、量大 | 質素優先、精品 |

## 流程（現階段＝手動觸發，未自動化）

1. **選故事**：Claude 睇最近未處理嘅 `story_type='short'`，用三準則揀最高分——①有具體道具/場景貫穿全篇（畫得出）②情感靠場面動作帶出，唔靠「隱藏資訊揭盅」式反轉（壓縮後唔失色）③情節密度低，7–8 鏡交代得晒。**懸疑反轉類唔啱**（揭盅位壓縮後衝擊力大減）。
2. **寫 storyboard**（Claude 親手做，唔係 script call LLM，對齊 `novel-story-generator`／shortdrama 模式）：拆 7 個 beat，每個含 `narration`（旁白）、`image_prompt`、`camera`（運鏡）、`has_protagonist`。存 `scripts/<story_id>.json`。
   - **image_prompt 結構**（精準度關鍵）：景別開頭（medium/close-up/wide + 角度）→ 動作場景 → **表情情緒**（唔好淨寫動作）→ 光線。
   - **主角一致性**：`episode.protagonist_lock` 寫一段好詳細嘅固定主角外貌（臉型/眼/髮/特徵/妝/衫），每個 `has_protagonist:true` 嘅 beat 自動 prepend。免費 model 冇 reference-lock，靠文字 lock + 固定 seed 拉近，唔會 100% 一致。
3. **送審**（現階段）：storyboard 出咗先俾 Stephanie 睇，批咗先生圖。試順咗先升自動（Telegram inline 批准掣 + listener，見下「未來自動化」）。
4. **生圖**：`python3 image_gen.py scripts/xxx.json`，逐 beat call Cloudflare Workers AI `@cf/black-forest-labs/flux-2-klein-9b`（免費層，multipart/form-data，1088x1920）。CF 失敗自動 fallback pollinations sana。`--beat N` 試單張、`--engine sana` 強制 fallback。
   - ⚠️ **CF 免費額度每日 10,000 neurons ≈ 8–10 張 flux-2 圖**，啱夠一日一集（7 張），但唔夠同日大量試錯／重生。爆額 4006 error → 等 UTC 零時 reset。
5. **旁白**：`python3 tts_gen.py scripts/xxx.json`，EdgeTTS（免費，`zh-CN-XiaoxiaoNeural` 普通話女聲）逐 beat 生 mp3 + 量實際秒數寫 `durations.json`。⚠️ 雲端 sandbox 要行 proxy（script 自動偵測 `https_proxy`）；Mac 本機直連。
6. **併片**：`python3 assemble.py output/<story_id>`，每 beat 做 Ken Burns 運鏡（6 種輪替：推近/掃右/上搖/拉遠/掃左/下搖，帶手持晃動）＋暗角＋菲林顆粒＋燒字幕（自動分行）＋首尾淡入淡出過黑轉場，concat 做 `final.mp4`（crf 25，一集 ~15MB，啱上社交平台）。
7. **出街**：手動上 IG Reels／抖音／YouTube Shorts。

## 成本估算

**全免費**（CF Workers AI 免費層 + EdgeTTS + ffmpeg + pollinations fallback）。唯一限制係 CF 每日 ~8–10 張圖額度。

## 裝置需求

```bash
pip install -r requirements.txt   # edge-tts + mutagen + python-dotenv
brew install ffmpeg               # assemble.py 需要;要 Noto Sans CJK/PingFang 字型燒字幕
```

`.env` 要有 `CF_ACCOUNT_ID` + `CF_API_TOKEN`（gitignored，同 daily-novel 根 `.env` 分開）。

## 資料來源

讀 `novel_stories` 直接用 Supabase MCP query project `cmtubaxlniglklmdwlzs`（同 novel-web 共用）。`source.story_id` 可循 Supabase 查返原文對照。

## 未來自動化（試順咗先做）

- Telegram `novel-video-bot`（Stephanie 揀 1b：開專屬 bot）送 storyboard + inline 批准掣。
- bot listener（收 ✅ callback → 觸發生圖 pipeline）+ 每日 scheduled task。呢兩樣同要一個長駐後台服務，一齊做最抵。
- Supabase `novel_video_jobs` 表（job 狀態）+ storage bucket（存片）+ `service_heartbeat`（task_name=`novel-video-clip`，掛 `check_novel_story_heartbeat.py` 多 job 監察）。

## 推送

跟 daily-novel 根目錄 `github_push.py`，冇獨立 push 機制。`output/` 同 `.env` 已 gitignore。
