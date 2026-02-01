#!/usr/bin/env python3
"""
本地測試：向 GAS Web App 的 doGet 發送 GET 請求，印出回傳的 JSON。
使用方式：
  1. 在 GAS 編輯器部署為「網路應用程式」，取得部署 URL。
  2. 設定網址（擇一或兩者）：
     - GAS_WEBAPP_DEV_URL：測試用，pytest 時優先使用。
     - GAS_WEBAPP_URL：正式用；未設 DEV 時 fallback 使用。
     - 在 .env 寫入上述變數，或執行前設環境變數。
  3. 執行：python tests/test_doget.py  或  pytest tests/test_doget.py
"""
import json
import os
import sys

import pytest

try:
    import requests
except ImportError:
    print("請先安裝 requests: pip install requests")
    sys.exit(1)

# 從 .env 載入（若存在），再讀環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 測試優先用 DEV，未設則用正式；結尾應為 /exec
WEBAPP_URL = os.environ.get("GAS_WEBAPP_DEV_URL") or os.environ.get("GAS_WEBAPP_URL", "")


def test_doget(url: str | None = None, params: dict | None = None) -> None:
    """向 GAS doGet 發送 GET，印出 JSON 結果。未設定 GAS_WEBAPP_URL 時跳過（供本地 unittest 全過）。"""
    base = url or WEBAPP_URL
    if not base:
        pytest.skip("請設定 GAS_WEBAPP_DEV_URL 或 GAS_WEBAPP_URL（或傳入 url）。例：GAS_WEBAPP_DEV_URL=https://script.google.com/macros/s/xxx/exec")
    # 確保是 /exec 端點
    if not base.rstrip("/").endswith("/exec"):
        base = base.rstrip("/") + "/exec"
    payload = params or {"status": "ok", "name": "test"}
    print("GET", base)
    print("Params:", payload)
    r = requests.get(base, params=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    print("Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if not WEBAPP_URL:
        print("請設定 GAS_WEBAPP_DEV_URL 或 GAS_WEBAPP_URL（或傳入 url）。")
        print("例：GAS_WEBAPP_DEV_URL=https://script.google.com/macros/s/xxx/exec python tests/test_doget.py")
        sys.exit(1)
    test_doget(params={"status": "ok", "name": "cursor_test"})
