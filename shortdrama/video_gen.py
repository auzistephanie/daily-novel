#!/usr/bin/env python3
"""
video_gen.py — 讀 storyboard JSON,逐鏡call fal.ai生成短劇片段

用法:
    python3 video_gen.py storyboards/2026-07-17_ti-jia-xian-hun-hou-ai.json
    python3 video_gen.py storyboards/xxx.json --dry-run   # 唔真係call API,淨係印出會call嘅內容(用嚟驗證storyboard格式)
    python3 video_gen.py storyboards/xxx.json --shot 3     # 淨生成第3鏡(慳成本試單鏡)

需要:
    pip install fal-client
    .env 入面要有 FAL_KEY=<你嘅 fal.ai API key>

流程:
    1. 讀 storyboard JSON 嘅 shots[]
    2. 每個 shot 用 characters[] 嘅 ref_prompt 拼埋 shot 嘅 video_prompt
    3. call fal.ai(預設 fal-ai/ltx-2.3/image-to-video,Fast tier)生成單鏡
    4. 存落 output/<story_id>/shot_<shot_id>.mp4
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

FAL_MODEL = "fal-ai/ltx-2.3/image-to-video"  # Fast tier,$0.04/秒起(1080p)


def load_storyboard(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_full_prompt(shot, characters_by_id):
    char_descs = []
    for cid in shot.get("characters", []):
        char = characters_by_id.get(cid)
        if char:
            char_descs.append(char["ref_prompt"])
    prompt_parts = char_descs + [shot["video_prompt"]]
    if shot.get("dialogue"):
        prompt_parts.append(f"dialogue (native lip-sync): {shot['dialogue']}")
    return " | ".join(prompt_parts)


def generate_shot(shot, full_prompt, out_dir, fal_key, dry_run=False):
    out_path = out_dir / f"shot_{shot['shot_id']:02d}.mp4"
    if dry_run:
        print(f"[DRY-RUN] shot {shot['shot_id']} ({shot['scene']}) -> {out_path}")
        print(f"          duration={shot['duration_sec']}s")
        print(f"          prompt={full_prompt[:160]}...")
        return

    import fal_client

    os.environ["FAL_KEY"] = fal_key
    result = fal_client.subscribe(
        FAL_MODEL,
        arguments={
            "prompt": full_prompt,
            "duration": shot["duration_sec"],
        },
        with_logs=True,
    )
    video_url = result.get("video", {}).get("url")
    if not video_url:
        raise RuntimeError(f"shot {shot['shot_id']} 冇攞到video url: {result}")

    import urllib.request
    urllib.request.urlretrieve(video_url, out_path)
    print(f"shot {shot['shot_id']} 生成完成 -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="讀storyboard JSON,逐鏡call fal.ai生成短劇片段")
    parser.add_argument("storyboard", help="storyboard JSON 路徑")
    parser.add_argument("--dry-run", action="store_true", help="唔call API,淨係印出會生成嘅內容")
    parser.add_argument("--shot", type=int, help="淨生成呢一個 shot_id")
    args = parser.parse_args()

    board = load_storyboard(args.storyboard)
    story_id = board["source"]["story_id"]
    characters_by_id = {c["id"]: c for c in board["characters"]}

    out_dir = Path(__file__).parent / "output" / story_id
    out_dir.mkdir(parents=True, exist_ok=True)

    fal_key = os.environ.get("FAL_KEY")
    if not args.dry_run and not fal_key:
        print("錯誤: 冇FAL_KEY(可以喺.env度set,或者export FAL_KEY=xxx)", file=sys.stderr)
        sys.exit(1)

    shots = board["shots"]
    if args.shot:
        shots = [s for s in shots if s["shot_id"] == args.shot]
        if not shots:
            print(f"錯誤: 搵唔到shot_id={args.shot}", file=sys.stderr)
            sys.exit(1)

    for shot in shots:
        full_prompt = build_full_prompt(shot, characters_by_id)
        generate_shot(shot, full_prompt, out_dir, fal_key, dry_run=args.dry_run)

    print(f"\n完成 {len(shots)} 個鏡頭 (story: {board['source']['title']})")


if __name__ == "__main__":
    main()
