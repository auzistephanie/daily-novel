# daily-novel 2026 追更爆款重整 Roadmap（提案 · 未執行）

> 目標：由「短篇小說機」→「令人追嘅短劇引擎」。
> 決勝點：**追更迴圈（retention）**，唔係單篇質量（已達頂）。
> 執行原則：逐 Phase 出 code preview → Stephanie confirm → 先改 → 用家身份 review → 更新 CLAUDE.md + push git。

---

## 核心判斷（作家視角）

| 現況 | 2026 爆款要求 | 缺口 |
|---|---|---|
| 3000-4500 字一次過完結 | 800-1200 字/集，收喺 cliffhanger | **無追更** |
| 人物每篇獨立 | 連續主角/世界觀，逼你返嚟 | **無回訪理由** |
| 鉤子只喺開場+結尾 | 每 200-300 字一個情緒點/小反轉 | **鉤子密度低** |
| 評分 → winner DNA | 開篇率/完讀率/追更率驅動 | **量度唔到「乜令人追」** |
| 男頻無末世腦洞、女頻單強虐渣 | 男頻腦洞末世/都市情緒；女頻雙強 | **題材缺 2026 爆點** |

---

## Phase 1 — 連載追更引擎（最高回報，先做）

**目標**：一個「系列」= 連續主角 + 世界觀，每集收喺鉤位，Telegram「▶️ 下一集」即時解鎖。

**改動檔案**
- `novel_generator.py`：新增 `generate_episode(series_id, ep_num)`；prompt 由「完整故事」改為「單集 800-1200 字 + 強制 cliffhanger 收尾 + 上集 recap 種子」；新增 `SERIES_ARC`（3-6 集弧線骨架池：虐→反擊→揭底→終局）。
- `utils.py`：新增 `save_series()` / `load_series()`（Redis 存 series 狀態：主角、arc、已出集數、下一集鉤子）。
- `bot_listener.py`：新增 `▶️ 下一集` callback + `/series` 指令（睇我追緊嘅系列）；生成時 header 顯示「第 N 集 · 系列名」。
- `genre_data.json` schema：加 `series` 節點。

**新增用家體驗**：`/now` 開新系列 → 每集尾「▶️ 下一集」→ 追到 arc 完 → 「本系列完結，開下一個？」

**工程量**：中 · **風險**：低（純加功能，唔郁現有單篇邏輯，保留 `/now` 舊行為做 fallback）

---

## Phase 2 — 題材升級 + 短劇節奏

**目標**：補 2026 爆點題材，鉤子密度由「頭尾」→「全篇」。

**改動檔案**
- `novel_generator.py`：
  - `GENRES` 加：男頻「末世腦洞」「都市情緒流」（w2）；女頻「雙強對峙」「雙潔對照」（w2）。對應 2026 市場：男頻腦洞末世/都市情緒爆、女頻由單強虐渣轉雙強。
  - 新增 `HOOK_DENSITY_RULE`：強制每 200-300 字一個「情緒點/資訊反轉/懸念」，接入男女頻 prompt。
  - 女頻 prompt 加「雙強」變體：男主唔係純追悔工具，係勢均力敵對手。
- `utils.py`：`fetch_trending_topics()` 熱搜關鍵詞池同步加末世/腦洞/雙強。

**工程量**：低-中 · **風險**：低（池擴充 + prompt 條款，向後兼容）

---

## Phase 3 — 留存數據系統

**目標**：由「評分驅動」→「留存驅動」，量度真正令人追嘅嘢。

**改動檔案**
- `utils.py` + `bot_listener.py`：追蹤三個訊號
  - **開篇率**：發出 vs 有人點開/回應
  - **完讀率**：睇到「下一集」按鈕 vs 追落去
  - **追更率**：一個系列平均追幾多集先棄
- `genre_data.json`：加 `metrics` 節點；winner 學習由「高評分 DNA」→「高追更率 DNA」加權。
- `bot_listener.py`：`/stats` 加留存面板（邊個系列/題材/鉤子類型最黐人）。

**工程量**：中 · **風險**：低-中（要小心 Redis 讀寫量；先做 minimal 訊號）

---

## 交付節奏（每 Phase）

1. 出該 Phase 詳細 code diff preview → 你 confirm
2. 改 code → 我用家身份實跑（真開一個系列、追 3 集、睇 output）驗證
3. 通過 → 更新 `CLAUDE.md` 改版歷史 → `python3 github_push.py`
4. 再入下一 Phase

---

## 建議起步

**Phase 1 先行**——回報最高、風險最低，一做即刻有「追」嘅感覺。你 confirm 我就出 Phase 1 嘅 `generate_episode` + series 存檔 + 「下一集」按鈕嘅完整 code preview。
