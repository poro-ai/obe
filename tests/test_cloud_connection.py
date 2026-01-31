#!/usr/bin/env python3
"""
GCF parse_pdf 全路徑連線測試：對已部署的 Cloud Function 發送 POST，驗證是否可連上。
使用方式：python tests/test_cloud_connection.py [BASE_URL]
預設 URL：https://us-central1-obe-project-485614.cloudfunctions.net/parse_pdf
"""
import json
import os
import sys

try:
    import requests
except ImportError:
    print("請先安裝 requests: pip install requests")
    sys.exit(1)

DEFAULT_URL = "https://us-central1-obe-project-485614.cloudfunctions.net/parse_pdf"


def test_parse_pdf_connection(base_url: str | None = None) -> bool:
    """對 parse_pdf 發送 POST，驗證連線。回傳 True 表示收到回應（2xx/4xx/5xx 皆視為連通）。"""
    url = (base_url or os.environ.get("GCF_PARSE_PDF_URL") or DEFAULT_URL).rstrip("/")
    if not url.endswith("/parse_pdf"):
        url = f"{url}/parse_pdf" if not url.endswith("/") else f"{url}parse_pdf"
    payload = {"bucket": "obe-files", "blob_path": "test/connection-check.pdf"}
    try:
        r = requests.post(url, json=payload, timeout=30)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        print(f"Status: {r.status_code}")
        print(f"Response: {json.dumps(body, indent=2, ensure_ascii=False)}")
        if r.status_code == 200:
            print("[OK] GCF 連線正常，並回傳 200。")
            return True
        if r.status_code in (400, 404, 500):
            print("[OK] GCF 已連通（端點有回應，邏輯或參數導致非 200）。")
            return True
        print(f"[WARN] 未預期狀態碼: {r.status_code}")
        return False
    except requests.RequestException as e:
        print(f"[FAIL] 連線失敗: {e}")
        return False


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    ok = test_parse_pdf_connection(url_arg)
    sys.exit(0 if ok else 1)
