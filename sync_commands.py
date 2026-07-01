#!/usr/bin/env python3
"""同步 Telegram「/」指令 menu（setMyCommands）——毋須重啟 bot。

Telegram 個「/」自動完成 menu 係由 setMyCommands API 設定，同 bot process 分開。
`bot_listener.register_commands()` 只喺 bot 啟動時行一次；改完指令但未重啟 bot，
menu 就唔會變。跑呢個腳本即刻同步（單一事實來源 = register_commands 個 list）：

    python3 sync_commands.py
"""
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

from bot_listener import register_commands

if __name__ == "__main__":
    register_commands()
    print("✅ Telegram 指令 menu 已同步（setMyCommands）")
