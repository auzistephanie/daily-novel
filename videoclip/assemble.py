#!/usr/bin/env python3
"""
assemble.py — 將 images/ + 旁白mp3 + durations.json 用 ffmpeg 砌做逐段 Ken Burns 短片,再併埋做 final.mp4

用法:
    python3 assemble.py output/<story_id>

要求:
    - 系統裝咗 ffmpeg(brew install ffmpeg / apt install ffmpeg)
    - 已經行過 image_gen.py 同 tts_gen.py(images/beat_NN.jpg、beat_NN.mp3、durations.json 齊晒)
    - 需要 Noto Sans CJK / PingFang 字型(燒字幕用);搵唔到就輸出冇字幕版本

輸出:
    <story_id>/beats/beat_NN.mp4 — 每段獨立片(運鏡 + 燒字幕 + 光效 + 配旁白)
    <story_id>/final.mp4 — 跟 beat 次序併埋嘅成品(過黑轉場,crf25 ~15MB)
"""
from __future__ import annotations  # 兼容 Mac 系統 python3.9(冇 PEP604 `X | None`)
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
]
FPS = 25
FADE_SEC = 0.4  # 每個分鏡首尾淡入淡出秒數(過黑轉場)
MAX_CHARS_PER_LINE = 15  # 1080px 闊、fontsize 40 底下嘅安全行寬


def wrap_subtitle(text: str, max_chars: int = MAX_CHARS_PER_LINE) -> str:
    """將旁白文字包做多行,盡量喺標點附近斷行,避免一行過長頂出畫面。"""
    break_chars = "、,,——。!!??"
    lines: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if len(buf) >= max_chars:
            cut = -1
            for i in range(len(buf) - 1, max(len(buf) - 6, 0) - 1, -1):
                if buf[i] in break_chars:
                    cut = i + 1
                    break
            if cut == -1:
                cut = len(buf)
            lines.append(buf[:cut])
            buf = buf[cut:]
    if buf:
        lines.append(buf)
    return "\n".join(lines)


def find_font() -> str | None:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return f
    return None


# ── 運鏡 preset ──────────────────────────────────────────────
# zoompan 靠 z/x/y 表達式做 Ken Burns。減 jitter:先 scale 到 2x(2160x3840)再 zoompan,
# output size 取整帶嚟嘅抖動被高解析度攤薄。on=當前幀序號,d=總幀數,zoom 由 1 起。
# 每個 beat 揀一種運鏡,輪替避免全片單調;beat.camera 可喺 storyboard 指定,冇就按 index 輪。
SS = "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840"


def camera_expr(kind: str, frames: int) -> str:
    """回傳 zoompan 嘅參數字串(唔含 d/s/fps)。所有運鏡都帶輕微手持晃動(sin 擺動)。"""
    d = frames
    shake_x = "+3*sin(on/20)"
    shake_y = "+3*cos(on/17)"
    presets = {
        "zoom_in": f"z='min(1+0.0016*on,1.28)':x='iw/2-(iw/zoom/2){shake_x}':y='ih/2-(ih/zoom/2){shake_y}'",
        "zoom_out": f"z='if(eq(on,0),1.28,max(1.28-0.0016*on,1.05))':x='iw/2-(iw/zoom/2){shake_x}':y='ih/2-(ih/zoom/2){shake_y}'",
        "pan_right": f"z='1.18':x='(iw-iw/zoom)*(on/{d}){shake_x}':y='ih/2-(ih/zoom/2){shake_y}'",
        "pan_left": f"z='1.18':x='(iw-iw/zoom)*(1-on/{d}){shake_x}':y='ih/2-(ih/zoom/2){shake_y}'",
        "pan_down": f"z='1.18':x='iw/2-(iw/zoom/2){shake_x}':y='(ih-ih/zoom)*(on/{d}){shake_y}'",
        "pan_up": f"z='1.18':x='iw/2-(iw/zoom/2){shake_x}':y='(ih-ih/zoom)*(1-on/{d}){shake_y}'",
    }
    return presets.get(kind, presets["zoom_in"])


# 冇指定 camera 時嘅輪替次序(推、掃右、上搖、拉遠、掃左、下搖)
CAMERA_CYCLE = ["zoom_in", "pan_right", "pan_up", "zoom_out", "pan_left", "pan_down"]


def build_beat_clip(story_dir: Path, beat: dict, duration: float, font: str | None, index: int = 0) -> Path:
    beat_id = beat["beat_id"]
    img = story_dir / "images" / f"beat_{beat_id:02d}.jpg"
    audio = story_dir / f"beat_{beat_id:02d}.mp3"
    beats_dir = story_dir / "beats"
    beats_dir.mkdir(exist_ok=True)
    out_path = beats_dir / f"beat_{beat_id:02d}.mp4"

    sub_path = beats_dir / f"beat_{beat_id:02d}_sub.txt"
    sub_path.write_text(wrap_subtitle(beat["narration"]), encoding="utf-8")

    frames = max(int(round(duration * FPS)), 1)
    cam = beat.get("camera") or CAMERA_CYCLE[index % len(CAMERA_CYCLE)]
    zp = camera_expr(cam, frames)
    fade = min(FADE_SEC, duration / 3)
    fade_out_st = max(duration - fade, 0)
    # 運鏡(SS放大減jitter -> zoompan)-> 暗角 -> 菲林顆粒(temporal noise)-> 首尾淡入淡出過黑
    vf = (
        f"{SS},zoompan={zp}:d={frames}:s=1080x1920:fps={FPS},"
        f"vignette=PI/5,noise=alls=6:allf=t"
    )
    if font:
        vf += (
            f",drawtext=fontfile={font}:textfile={sub_path}:fontcolor=white:fontsize=40:"
            f"line_spacing=10:x=(w-text_w)/2:y=h-340:box=1:boxcolor=black@0.45:boxborderw=16"
        )
    vf += f",fade=t=in:st=0:d={fade:.2f},fade=t=out:st={fade_out_st:.2f}:d={fade:.2f}"
    af = f"afade=t=in:st=0:d=0.15,afade=t=out:st={fade_out_st:.2f}:d={fade:.2f}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img),
        "-i", str(audio),
        "-filter_complex", f"[0:v]{vf}[v];[1:a]{af}[a]",
        "-map", "[v]", "-map", "[a]",
        # crf 25:菲林顆粒會推高碼率,唔控制 final 會爆 30MB+;crf 25 畫質仍然好,一集 ~15MB 啱上社交平台
        "-c:v", "libx264", "-crf", "25", "-preset", "medium",
        "-t", f"{duration}", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def concat_clips(story_dir: Path, clip_paths: list[Path]) -> Path:
    concat_list = story_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve()}'\n")

    out_path = story_dir / "final.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="砌Ken Burns短片+燒字幕,併做final.mp4")
    parser.add_argument("story_dir", help="story output 資料夾,例如 output/<story_id>")
    parser.add_argument("--script", help="beats JSON 路徑(預設自動喺 ../../scripts/<story_id>.json 搵)")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("錯誤: 搵唔到 ffmpeg,請先安裝(brew install ffmpeg)", file=sys.stderr)
        sys.exit(1)

    story_dir = Path(args.story_dir)
    story_id = story_dir.name
    script_path = Path(args.script) if args.script else story_dir.parent.parent / "scripts" / f"{story_id}.json"
    board = json.loads(script_path.read_text(encoding="utf-8"))
    durations = json.loads((story_dir / "durations.json").read_text(encoding="utf-8"))

    font = find_font()
    if not font:
        print("⚠️ 搵唔到 Noto Sans CJK / PingFang 字型,將輸出冇字幕版本", file=sys.stderr)

    clip_paths = []
    for index, beat in enumerate(board["beats"]):
        dur = durations.get(str(beat["beat_id"]))
        if dur is None:
            print(f"錯誤: durations.json 冇 beat {beat['beat_id']}", file=sys.stderr)
            sys.exit(1)
        clip = build_beat_clip(story_dir, beat, dur, font, index)
        cam = beat.get("camera") or CAMERA_CYCLE[index % len(CAMERA_CYCLE)]
        print(f"beat {beat['beat_id']} 砌好({cam}) -> {clip} ({dur:.2f}s)")
        clip_paths.append(clip)

    final = concat_clips(story_dir, clip_paths)
    total = sum(durations.values())
    print(f"\n併片完成 -> {final} ({len(clip_paths)} 段, 約 {total:.1f}s)")


if __name__ == "__main__":
    main()
