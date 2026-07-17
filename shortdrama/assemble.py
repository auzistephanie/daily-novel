#!/usr/bin/env python3
"""
assemble.py — 將 output/<story_id>/shot_*.mp4 用 ffmpeg 併埋做一條成品短劇

用法:
    python3 assemble.py output/3d98fe2f-0012-4728-bc67-60533fae70a6

要求:
    - 需要系統裝咗 ffmpeg (brew install ffmpeg)
    - shot_*.mp4 檔名要跟 video_gen.py 出嘅格式 (shot_01.mp4, shot_02.mp4 ...)

輸出:
    <story_id>/final.mp4 (跟拍攝次序併埋,冇轉場特效嘅版本;想加轉場/字幕/BGM,呢個script先得基本版,按需擴充)
"""
import argparse
import subprocess
import sys
from pathlib import Path


def assemble(shot_dir: Path):
    shots = sorted(shot_dir.glob("shot_*.mp4"))
    if not shots:
        print(f"錯誤: {shot_dir} 入面搵唔到 shot_*.mp4", file=sys.stderr)
        sys.exit(1)

    concat_list = shot_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for shot in shots:
            f.write(f"file '{shot.resolve()}'\n")

    out_path = shot_dir / "final.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(out_path),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"併片完成 -> {out_path} ({len(shots)} 個鏡頭)")


def main():
    parser = argparse.ArgumentParser(description="將shot_*.mp4併做一條成品短劇")
    parser.add_argument("shot_dir", help="存住 shot_*.mp4 嘅資料夾,例如 output/<story_id>")
    args = parser.parse_args()
    assemble(Path(args.shot_dir))


if __name__ == "__main__":
    main()
