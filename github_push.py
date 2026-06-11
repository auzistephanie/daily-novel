#!/usr/bin/env python3
"""Push current repo changes to GitHub via API (bypasses git CLI lock issues)."""
import os, sys, base64, subprocess, json
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = "auzistephanie"
REPO = "daily-novel"
BRANCH = "main"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))

def main():
    if not TOKEN:
        print("ERROR: GitHub token not found in .env (GITHUB_TOKEN)")
        sys.exit(1)

    msg = sys.argv[1] if len(sys.argv) > 1 else "Update"

    status = run("git status --porcelain")
    if not status.stdout.strip():
        print("Nothing to commit, repo is up to date.")
        return

    changes = []
    for line in status.stdout.strip().split("\n"):
        x, y, path = line[0], line[1], line[2:].strip()
        path = path.split(" -> ")[-1]
        st = (x + y).strip()
        if st == "??" or "A" in st or "M" in st:
            changes.append(("upsert", path))
        elif "D" in st:
            changes.append(("delete", path))

    ref = requests.get(f"{API}/git/ref/heads/{BRANCH}", headers=HEADERS).json()
    base_sha = ref["object"]["sha"]
    base_commit = requests.get(f"{API}/git/commits/{base_sha}", headers=HEADERS).json()
    base_tree = base_commit["tree"]["sha"]

    tree_items = []
    for action, path in changes:
        if action == "upsert":
            with open(path, "rb") as f:
                content = f.read()
            blob = requests.post(f"{API}/git/blobs", headers=HEADERS, json={
                "content": base64.b64encode(content).decode(),
                "encoding": "base64"
            }).json()
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
            print(f"  modified/added: {path}")
        else:
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            print(f"  deleted: {path}")

    new_tree = requests.post(f"{API}/git/trees", headers=HEADERS, json={
        "base_tree": base_tree, "tree": tree_items
    }).json()

    new_commit = requests.post(f"{API}/git/commits", headers=HEADERS, json={
        "message": msg, "tree": new_tree["sha"], "parents": [base_sha]
    }).json()

    requests.patch(f"{API}/git/refs/heads/{BRANCH}", headers=HEADERS, json={"sha": new_commit["sha"]})

    print(f"✅ Pushed to GitHub — {msg}")

if __name__ == "__main__":
    main()
