#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""掃描專案中超過 10MB 的二進位/大檔案，提醒移至 GCS 或加入忽略。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE_MB = 10
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "ENV", "env", "__pycache__", ".pytest_cache"}


def main():
    os.chdir(ROOT)
    large = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(s in path.parts for s in SKIP_DIRS):
            continue
        try:
            if path.stat().st_size > SIZE_MB * 1024 * 1024:
                large.append((path, path.stat().st_size))
        except OSError:
            continue

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    if not large:
        print("未發現超過 10MB 的檔案。")
        return
    print("以下檔案超過 10MB，建議移至 GCS 或加入 .cursorignore/.gitignore：")
    for path, size in sorted(large, key=lambda x: -x[1]):
        mb = size / (1024 * 1024)
        print(f"  {path.relative_to(ROOT)}  ({mb:.1f} MB)")
    print("\n可將副檔名加入 .cursorignore 與 .gitignore，或將檔案上傳至 GCS 後自本地刪除。")


if __name__ == "__main__":
    main()
