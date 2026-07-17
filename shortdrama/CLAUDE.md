# CLAUDE.md — shortdrama（短劇 video pipeline）

由 daily-novel/novel-web 現有文字故事庫（Supabase `novel_stories`）做劇本源頭,轉做AI生成短劇video嘅子系統。2026-07-17 開設,唔屬於novel-web嘅git版本控制範圍(獨立subfolder,跟daily-novel repo一齊push)。

## 流程

1. **選故事**：從 Supabase `novel_stories` 揀一篇（建議 `story_type='short'`，情感向 genre 對應 Voice D，最啱短劇單元劇格式）
2. **寫storyboard**（Claude直接做,唔係script）：讀故事content,拆做分鏡JSON(鏡頭ID/景別/video_prompt/角色/對白/BGM),存落`storyboards/`。跟返novel-web嘅Voice house rule(情緒用動作代替,唔直寫「佢好感動」)。呢步做法對齊`novel-story-generator` scheduled task 嘅模式——Claude親自生成內容,唔係靠python call LLM API。
3. **生成片段**：`python3 video_gen.py storyboards/xxx.json`,逐鏡call fal.ai(預設`fal-ai/ltx-2.3/image-to-video` Fast tier,$0.04/秒起1080p)。`--dry-run`可以唔洗key試跑格式;`--shot N`可以淨試一鏡慳成本。
4. **併片**：`python3 assemble.py output/<story_id>`,用ffmpeg跟拍攝次序concat做`final.mp4`(基本版,冇轉場/字幕/BGM混音,按需擴充)
5. **出街**：novel-web網站冇片播放功能,片人手上IG Reels/抖音/YouTube Shorts

## 成本估算

一集2分鐘(≈24條5秒鏡頭=120秒) LTX-2.3 Fast ≈ $4.8美金。單集試跑(10鏡,~50秒) ≈ $2美金內。

## 裝置需求

```bash
pip install -r requirements.txt   # fal-client + python-dotenv
brew install ffmpeg               # assemble.py 需要
```

`.env` 要有 `FAL_KEY`(fal.ai API key,gitignored,同daily-novel根目錄嘅.env分開)。

## 資料來源

讀 `novel_stories` 唔經呢個repo嘅任何本機檔案——直接用Supabase MCP query project `cmtubaxlniglklmdwlzs`(同novel-web共用)。Storyboard入面`source.story_id`可以循Supabase查返原文對照。

## 推送

跟daily-novel根目錄`github_push.py`,冇獨立push機制。`output/`同`.env`已gitignore,唔會上repo(片太大)。
