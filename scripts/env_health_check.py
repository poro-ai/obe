#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專案環境配置體檢：掃描程式碼使用的環境變數、比對 .env、架構完整性與安全性檢查。
"""
import os
import re
import sys
from pathlib import Path

# Windows 終端機 UTF-8 輸出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 專案根目錄（腳本在 scripts/）
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ENV_FILE = ROOT / ".env"
GITIGNORE = ROOT / ".gitignore"

# 架構關鍵變數（GCF + Gemini + GCS + Sheets）
ARCHITECTURE_VARS = {
    "ENV_MODE": "切換本地/雲端模式（local | production）",
    "GEMINI_API_KEY": "Gemini API 金鑰",
    "GEMINI_MODEL_NAME": "預設模型名稱（如 gemini-1.5-flash）",
    "PROJECT_ID": "GCP 專案 ID（Secret Manager / GCS 用）",
    "GCS_BUCKET_NAME": "GCS 預設桶子名稱",
    "GOOGLE_SHEET_ID": "寫入解析結果的 Google 試算表 ID",
    "GOOGLE_SHEET_NAME": "目標工作表名稱",
}
# 程式碼中透過 get_secret / os.environ 使用的變數（掃描結果可擴充）
CODE_VARS = {"ENV_MODE", "PROJECT_ID", "GOOGLE_CLOUD_PROJECT", "GEMINI_API_KEY"}


def scan_src_for_env_vars() -> set[str]:
    """掃描 src/ 下 os.getenv、os.environ、get_secret 使用的變數名。"""
    found = set()
    for py_file in SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        # os.environ.get("VAR") / os.getenv("VAR")
        for m in re.finditer(r'os\.(?:environ\.get|getenv)\s*\(\s*["\']([^"\']+)["\']', text):
            found.add(m.group(1))
        # get_secret("VAR")
        for m in re.finditer(r'get_secret\s*\(\s*["\']([^"\']+)["\']', text):
            found.add(m.group(1))
    return found


def parse_env_file() -> dict[str, str]:
    """解析 .env：KEY=VALUE，略過註解與空行。"""
    result = {}
    if not ENV_FILE.exists():
        return result
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip("'\"").strip()
    return result


def check_gitignore() -> tuple[bool, bool]:
    """檢查 .gitignore 是否排除 .env 與 venv/。"""
    if not GITIGNORE.exists():
        return False, False
    content = GITIGNORE.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    has_env = any(ln == ".env" or ln.startswith(".env") for ln in lines)
    has_venv = any("venv" in ln or ".venv" in ln for ln in lines)
    return has_env, has_venv


def main() -> None:
    os.chdir(ROOT)
    code_vars = scan_src_for_env_vars()
    env_values = parse_env_file()
    env_has_env, env_has_venv = check_gitignore()

    # 合併架構變數與程式碼掃描變數
    all_relevant = set(ARCHITECTURE_VARS) | code_vars

    configured = []
    missing = []
    for key in sorted(all_relevant):
        value = env_values.get(key, "")
        desc = ARCHITECTURE_VARS.get(key, "（程式碼或架構使用）")
        if value:
            configured.append((key, desc))
        else:
            missing.append((key, desc))

    # 輸出報告
    print("=" * 60)
    print("專案環境配置體檢報告")
    print("=" * 60)
    print()
    print("【1】程式碼掃描（src/ 內 os.getenv / get_secret 使用）")
    print("     變數名稱:", ", ".join(sorted(code_vars)) if code_vars else "（無）")
    print()
    print("【2】已設定的變數（.env 中有值）")
    if configured:
        for key, desc in configured:
            print(f"     • {key}")
            print(f"       作用: {desc}")
    else:
        print("     （無）")
    print()
    print("【3】缺失中的變數（未在 .env 或值為空）")
    if missing:
        for key, desc in missing:
            print(f"     • {key}")
            print(f"       作用: {desc}")
    else:
        print("     （無）")
    print()
    print("【4】架構完整性（GCF + Gemini + GCS + Sheets）")
    for key in ARCHITECTURE_VARS:
        status = "[OK] 已設定" if env_values.get(key, "").strip() else "[--] 缺失"
        print(f"     {key}: {status}")
    print()
    print("【5】安全性驗證（.gitignore）")
    print(f"     排除 .env:   {'[OK] 是' if env_has_env else '[X] 否'}")
    print(f"     排除 venv/: {'[OK] 是' if env_has_venv else '[X] 否'}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
