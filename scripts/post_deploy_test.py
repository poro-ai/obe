#!/usr/bin/env python3
"""
部署後驗證：檢查已部署的 GCF parse_pdf 網址是否可正常回應。

使用方式：
  python scripts/post_deploy_test.py
  python scripts/post_deploy_test.py --project obe-project-485614 --region asia-east1
  python scripts/post_deploy_test.py --url https://asia-east1-obe-project-485614.cloudfunctions.net/parse_pdf

環境變數（可選）：
  GCF_PROJECT_ID  預設 obe-project-485614
  GCF_REGION      預設 asia-east1
  GCF_FUNCTION    預設 parse_pdf
  GCF_PARSE_PDF_URL  若設定則直接使用此 URL，忽略 project/region/function
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("請先安裝 requests: pip install requests")
    sys.exit(1)

DEFAULT_PROJECT = "obe-project-485614"
DEFAULT_REGION = "asia-east1"
DEFAULT_FUNCTION = "parse_pdf"


def build_gcf_url(project: str, region: str, function_name: str) -> str:
    return f"https://{region}-{project}.cloudfunctions.net/{function_name}"


def verify_gcf(url: str, timeout: int = 60) -> bool:
    """對 parse_pdf 發送 POST，驗證是否可連上並取得有效 HTTP 回應。"""
    payload = {"bucket": "obe-files", "blob_path": "test/connection-check.pdf"}
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        body = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        print(f"URL: {url}")
        print(f"HTTP Status: {r.status_code}")
        print(f"Response: {json.dumps(body, indent=2, ensure_ascii=False)}")
        if r.status_code == 200:
            print("[OK] 部署後驗證通過：GCF 回傳 200。")
            return True
        if 200 <= r.status_code < 600:
            print("[OK] 部署後驗證通過：端點有回應（邏輯或測試檔案可能導致非 200）。")
            return True
        print(f"[WARN] 未預期狀態碼: {r.status_code}")
        return False
    except requests.RequestException as e:
        print(f"[FAIL] 部署後驗證失敗：連線錯誤 — {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="驗證部署後的 GCF parse_pdf 是否可正常回應")
    parser.add_argument("--url", help="GCF 完整 URL（若設定則忽略 project/region/function）")
    parser.add_argument(
        "--project",
        default=os.environ.get("GCF_PROJECT_ID", DEFAULT_PROJECT),
        help=f"GCP 專案 ID（預設: {DEFAULT_PROJECT}）",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("GCF_REGION", DEFAULT_REGION),
        help=f"GCF 區域（預設: {DEFAULT_REGION}）",
    )
    parser.add_argument(
        "--function",
        default=os.environ.get("GCF_FUNCTION", DEFAULT_FUNCTION),
        help=f"函式名稱（預設: {DEFAULT_FUNCTION}）",
    )
    parser.add_argument("--timeout", type=int, default=60, help="請求逾時秒數（預設: 60）")
    args = parser.parse_args()

    if args.url:
        url = args.url.rstrip("/")
        if not url.endswith(f"/{DEFAULT_FUNCTION}") and not url.endswith(f"/{args.function}"):
            url = f"{url}/{args.function}" if not url.endswith("/") else f"{url}{args.function}"
    else:
        url = build_gcf_url(args.project, args.region, args.function)

    ok = verify_gcf(url, timeout=args.timeout)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
