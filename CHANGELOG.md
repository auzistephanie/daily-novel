# 改版歷史

> 唔會自動讀入每次對話 context，需要時先 `read_file`。

- **2026-06-11**：取消每隔一日 9am 自動生成 cron，改為自己選擇時間按需生成
- **2026-06-11**：刪 6 個男頻冷門類別（醫術流／古言權謀／鑑寶奇才／神豪撒幣／末世崛起／競技熱血）；新增 10 個女頻言情爆款 + channel/weight 加權系統；加爆款標題公式；男女頻分開 prompt 模板。
- **2026-06-23**：刪甜寵逆襲（男頻，市場飽和）、玄學風水（冷門）；新增漫畫感爽文（M, w2）、重生年代稱霸（M, w2）、懸疑言情（F, w2）——對應 2026 短劇爆款趨勢。
- **2026-07-01**：刪重生年代稱霸（風格特殊，整合難度高）；/now 同 /lit 合併為隨機生成；加 CHARACTER_WOUNDS、TWIST_SEEDS、VILLAIN_MOTIVATIONS、SUSPENSE_HOOKS 池提升故事質量。
- **2026-07-02**：**Phase 1 追睇引擎**——由「短篇機」變「追劇機」。新增連載系統（`SERIES_ARCS` 7 條弧線 3-5 集，每集收 cliffhanger）+ 需求驅動（🤩 超好 → 續寫成連載）+ 讀者選擇分支（每集尾 2 選擇改寫下集）。新指令 `/series`。已用家身份實跑驗證：ep1 標題+選擇掣、ep2 接住讀者選擇、ep3 終集完結，劇情連貫、無殘留控制碼。對應 2026 短劇「密集反轉 + 追更留存」趨勢。
- **2026-07-02**：**Phase 2 題材+節奏**——GENRES 加末世腦洞(M,w2)／都市情緒流(M,w2)／雙強對峙(F,w2)（對應 2026 男頻腦洞末世＋都市情緒、女頻雙強爆點），共 28 類。新增 `HOOK_DENSITY_RULE` 注入單篇男女 prompt，令單篇都有短劇密集節奏。
- **2026-07-02**：**Phase 3 留存數據**——追蹤 start/continue/choice/complete 點擊事件（Redis `retention_metrics`），選類由評分驅動升級「追更率驅動」（`_retention_multiplier`＋`weighted_choice_retention`），`/stats` 加追更率／完讀率／互動率面板。離線驗證：埋點正確、黐人題材倍數 1.68、抽樣被選 3.2 倍。另加 `sync_commands.py` 解決改指令後 Telegram menu 唔更新（setMyCommands 獨立同步、毋須重啟 bot）。
- **2026-07-04**：**連載選擇對齊 + 防重複補強**——① 連載每集尾加 `<<<SCENE>>>` 控制碼強制模型先白描返正文最後一幕先出 NEXT/CA/CB，杜絕「選擇同正文脫節」；生成後用 bigram 重疊率驗證 CA/CB 有冇對應正文尾段，兩個都唔夾先觸發低溫度細 call 補救（`_choice_grounded`／`_regen_ending_hook`）。② 主角職業/性格/傷口（`generate_character`）同反派原型/開場鉤子（`generate_story`）套用返現有 `recent_dna` 防重複機制（sliding window 5），解決短期內故事「似返之前」問題。已用 mock Redis + 模擬 raw output 跑腳本驗證：parsing 正確、grounding 判斷符合預期、8 次連續生成 window-5 內無重複。
