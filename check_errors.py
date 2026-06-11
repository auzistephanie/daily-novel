"""
掃 bot_listener.log，過濾走 telegram connection 類 error，
剩低嘅當作 code-level exception 報俾 Stephanie。
記錄上次檢查行數於 .error_check_state，下次只睇新行。
"""
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "bot_listener.log")
STATE_FILE = os.path.join(os.path.dirname(__file__), ".error_check_state")

# 純網絡連線問題，唔算 code bug
NETWORK_KEYWORDS = [
    "HTTPSConnectionPool",
    "NameResolutionError",
    "NewConnectionError",
    "ConnectionResetError",
    "ConnectTimeoutError",
    "Read timed out",
    "Connection aborted",
    "No route to host",
    "Failed to resolve",
    "Operation timed out",
]


def main():
    if not os.path.exists(LOG_FILE):
        print("bot_listener.log 唔存在，無嘢做")
        return

    with open(LOG_FILE, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    last_pos = 0
    if os.path.exists(STATE_FILE):
        try:
            last_pos = int(open(STATE_FILE).read().strip())
        except ValueError:
            last_pos = 0

    new_lines = lines[last_pos:]

    real_errors = []
    for line in new_lines:
        if "Error" not in line and "Exception" not in line and "Traceback" not in line:
            continue
        if any(kw in line for kw in NETWORK_KEYWORDS):
            continue
        real_errors.append(line.rstrip())

    # 更新 state（無論有冇 error 都要記錄，避免重覆檢查）
    with open(STATE_FILE, "w") as f:
        f.write(str(len(lines)))

    if real_errors:
        print(f"發現 {len(real_errors)} 個 code-level error:")
        for e in real_errors:
            print(e)
    else:
        print("無新 code-level error（已過濾 telegram connection error）")


if __name__ == "__main__":
    main()
