#!/usr/bin/env python3
"""
tts_gen.py — 讀 beats JSON,逐段用 EdgeTTS(免費)生成旁白,並量返實際秒數

用法:
    python3 tts_gen.py scripts/<story_id>.json

需要:
    pip install edge-tts mutagen

⚠️ 環境注意(2026-07-21 已實測):Cowork 雲端 sandbox 淨係俾 HTTP(S) proxy 出網,
edge-tts 底層 aiohttp 預設唔會讀 https_proxy 環境變數,直連 speech.platform.bing.com
會撞 SSL 憑證錯誤。呢個 script 自動偵測 https_proxy/HTTPS_PROXY 環境變數,
有就傳俾 edge-tts;冇(例如喺 Mac 本機跑)就直連,兩種環境都得。

流程:
    1. 讀 beats[] 嘅 narration
    2. 用 edge-tts(zh-CN-XiaoxiaoNeural,可用 --voice 換)逐段生成 mp3
    3. 用 mutagen 量返實際秒數,寫入 output/<story_id>/durations.json
       (assemble.py 靠呢個檔知道每段 Ken Burns 該做幾長)
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


def load_script(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_proxy() -> str | None:
    return os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or None


async def synth_one(text: str, voice: str, out_path: Path, proxy: str | None) -> None:
    kwargs = {"proxy": proxy} if proxy else {}
    communicate = edge_tts.Communicate(text, voice, **kwargs)
    await communicate.save(str(out_path))


def main():
    parser = argparse.ArgumentParser(description="讀beats JSON,逐段生成EdgeTTS旁白(免費)")
    parser.add_argument("script", help="beats JSON 路徑")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"EdgeTTS 音色,預設 {DEFAULT_VOICE}")
    parser.add_argument("--beat", type=int, help="淨生成呢一個 beat_id")
    args = parser.parse_args()

    board = load_script(args.script)
    story_id = board["source"]["story_id"]

    out_dir = Path(__file__).parent / "output" / story_id
    out_dir.mkdir(parents=True, exist_ok=True)

    beats = board["beats"]
    if args.beat:
        beats = [b for b in beats if b["beat_id"] == args.beat]
        if not beats:
            print(f"錯誤: 搵唔到beat_id={args.beat}", file=sys.stderr)
            sys.exit(1)

    proxy = get_proxy()
    durations = {}
    for beat in beats:
        out_path = out_dir / f"beat_{beat['beat_id']:02d}.mp3"
        asyncio.run(synth_one(beat["narration"], args.voice, out_path, proxy))
        dur = MP3(str(out_path)).info.length
        durations[str(beat["beat_id"])] = round(dur, 3)
        print(f"beat {beat['beat_id']} 旁白生成完成 -> {out_path} ({dur:.2f}s)")

    durations_path = out_dir / "durations.json"
    existing = {}
    if durations_path.exists():
        existing = json.loads(durations_path.read_text(encoding="utf-8"))
    existing.update(durations)
    durations_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(existing.values())
    print(f"\n完成 {len(beats)} 段旁白 (story: {board['source']['title']}),累計時長 {total:.1f}s")


if __name__ == "__main__":
    main()
