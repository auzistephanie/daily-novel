#!/usr/bin/env python3
"""
image_gen.py — 讀 beats JSON,逐段用 Cloudflare Workers AI(免費層)生成 AI 圖

用法:
    python3 image_gen.py scripts/<story_id>.json
    python3 image_gen.py scripts/<story_id>.json --beat 3   # 淨生成第3段
    python3 image_gen.py scripts/<story_id>.json --engine sana   # 強制用 pollinations fallback

引擎:
    1. 主引擎:Cloudflare Workers AI `@cf/black-forest-labs/flux-2-klein-9b`
       - 免費層每日 10,000 neurons,原生支援 1088x1920(9:16)
       - 要 .env 有 CF_ACCOUNT_ID + CF_API_TOKEN(Workers AI 權限)
       - ⚠️ 呢個 model 要用 multipart/form-data(唔係 JSON body),2026-07-21 實測
    2. Fallback:pollinations.ai sana(免費免key,質素低啲)——CF 冇 key 或連續失敗時自動用

    圖用 episode.style_suffix 統一畫風 + protagonist_lock 描述保持主角一致(免費 model 冇
    真正嘅 character lock,靠一致描述詞 + 固定 seed 頂住,多鏡之間樣貌仍可能有少少漂移)。
"""
from __future__ import annotations  # 兼容 Mac 系統 python3.9(冇 PEP604 `X | None`)
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

CF_MODEL = "@cf/black-forest-labs/flux-2-klein-9b"
WIDTH = 1088   # flux-2 要 16 嘅倍數,1088x1920 係最接近 1080x1920 嘅有效 9:16
HEIGHT = 1920


def load_script(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cf_generate(prompt: str, out_path: Path, account_id: str, token: str,
                seed: int | None = None, timeout: int = 120) -> None:
    """Cloudflare Workers AI flux-2-klein-9b,multipart/form-data 格式。
    傳同一個 seed 有助多鏡之間畫風/主角一致(配合 protagonist_lock 文字描述)。"""
    boundary = uuid.uuid4().hex
    fields = {"prompt": prompt, "width": str(WIDTH), "height": str(HEIGHT)}
    if seed is not None:
        fields["seed"] = str(seed)
    parts = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
        )
    body = ("".join(parts) + f"--{boundary}--\r\n").encode("utf-8")

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{CF_MODEL}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.load(resp)
    if not result.get("success"):
        raise RuntimeError(f"CF 回應唔成功: {json.dumps(result)[:300]}")
    import base64
    out_path.write_bytes(base64.b64decode(result["result"]["image"]))


def sana_generate(prompt: str, out_path: Path, seed: int, timeout: int = 40) -> None:
    """pollinations.ai 免費 fallback(sana model)。"""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&seed={seed}&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "daily-novel-videoclip/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out_path.write_bytes(resp.read())


def generate_one(prompt: str, out_path: Path, seed: int, engine: str,
                 account_id: str | None, token: str | None) -> str:
    """試 CF 兩次,唔得先 fallback sana。回傳實際用咗邊個引擎。"""
    if engine != "sana" and account_id and token:
        last_err = None
        for attempt in range(2):
            try:
                cf_generate(prompt, out_path, account_id, token, seed=seed)
                return "cf-flux2"
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(3)
        print(f"⚠️ CF 生成失敗({last_err}),改用 pollinations fallback", file=sys.stderr)
    sana_generate(prompt, out_path, seed)
    return "sana"


def main():
    parser = argparse.ArgumentParser(description="讀beats JSON,逐段生成AI圖(CF flux-2 主/sana fallback)")
    parser.add_argument("script", help="beats JSON 路徑")
    parser.add_argument("--beat", type=int, help="淨生成呢一個 beat_id")
    parser.add_argument("--engine", choices=["cf", "sana"], default="cf", help="強制引擎")
    args = parser.parse_args()

    board = load_script(args.script)
    story_id = board["source"]["story_id"]
    seed = board["episode"].get("seed", 0)
    style_suffix = board["episode"].get("style_suffix", "")
    # protagonist_lock:全片統一主角外貌硬套(有主角出鏡嘅 beat 都 prepend),減少樣貌漂移。
    # 舊 storyboard 用 character_ref,做 fallback 相容。
    char_ref = board["episode"].get("protagonist_lock") or board["episode"].get("character_ref", "")

    account_id = os.environ.get("CF_ACCOUNT_ID")
    token = os.environ.get("CF_API_TOKEN")
    if args.engine == "cf" and not (account_id and token):
        print("⚠️ .env 冇 CF_ACCOUNT_ID/CF_API_TOKEN,全部用 pollinations fallback", file=sys.stderr)

    out_dir = Path(__file__).parent / "output" / story_id / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    beats = board["beats"]
    if args.beat:
        beats = [b for b in beats if b["beat_id"] == args.beat]
        if not beats:
            print(f"錯誤: 搵唔到beat_id={args.beat}", file=sys.stderr)
            sys.exit(1)

    for beat in beats:
        pieces = [beat["image_prompt"]]
        if char_ref and beat.get("has_protagonist", True):
            pieces.insert(0, char_ref)
        if style_suffix:
            pieces.append(style_suffix)
        full_prompt = ", ".join(pieces)
        out_path = out_dir / f"beat_{beat['beat_id']:02d}.jpg"
        used = generate_one(full_prompt, out_path, seed, args.engine, account_id, token)
        print(f"beat {beat['beat_id']} 生成完成({used}) -> {out_path}")

    print(f"\n完成 {len(beats)} 段圖 (story: {board['source']['title']})")


if __name__ == "__main__":
    main()
