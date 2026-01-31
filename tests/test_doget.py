#!/usr/bin/env python3
"""
本地測試：向 GAS Web App 的 doGet 發送 GET 請求，印出回傳的 JSON。
使用方式：
  1. 在 GAS 編輯器部署為「網路應用程式」，取得部署 URL。
  2. 設定環境變數 GAS_WEBAPP_URL 或於下方 WEBAPP_URL 填入 URL。
  3. 執行：python tests/test_doget.py
"""
import json
import os
import sys

try:
    import requests
except ImportError:
    print("請先安裝 requests: pip install requests")
    sys.exit(1)

# 部署後的 GAS Web App URL（結尾為 /exec）
WEBAPP_URL = os.environ.get("GAS_WEBAPP_URL", "")


def test_doget(url: str | None = None, params: dict | None = None) -> None:
    """向 GAS doGet 發送 GET，印出 JSON 結果。"""
    base = url or WEBAPP_URL
    if not base:
        print("請設定 GAS_WEBAPP_URL 或傳入 url 參數。")
        print("例：GAS_WEBAPP_URL=https://script.google.com/macros/s/xxx/exec python tests/test_doget.py")
        sys.exit(1)
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
    test_doget(params={"status": "ok", "name": "cursor_test"})
