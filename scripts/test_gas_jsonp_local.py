#!/usr/bin/env python3
"""
本機快速測試：對 GAS Web App 發送與編輯器相同的 JSONP 請求，驗證版本與解析結果。

使用方式（擇一）：
  1. 在專案根目錄建立 .env，寫入：
     GAS_WEBAPP_DEV_URL=https://script.google.com/macros/s/xxx/dev
     或 GAS_WEBAPP_URL=https://script.google.com/macros/s/xxx/exec
  2. 或執行時帶環境變數：
     set GAS_WEBAPP_DEV_URL=https://script.google.com/macros/s/xxx/dev
     python scripts/test_gas_jsonp_local.py

會依序測試：
  - 版本請求：GET url?callback=xxx → 預期回傳 JSONP，內含 version
  - 解析結果請求：GET url?action=getParseResult&token=bad&callback=yyy → 預期回傳 JSONP（error 或 pages）

若 GAS 回傳「純 JSON」而非「callback(JSON)」，編輯器在跨域時會無法解析，版號與解析結果都會抓不到。
"""
import json
import os
import re
import sys

try:
    import requests
except ImportError:
    print("請先安裝 requests: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _get_base_url() -> str:
    u = (os.environ.get("GAS_WEBAPP_DEV_URL") or os.environ.get("GAS_WEBAPP_URL") or "").strip()
    if len(sys.argv) > 1:
        u = sys.argv[1].strip()
    return u


def parse_jsonp(text: str, callback_name: str) -> dict | list | None:
    """解析 JSONP：callbackName({...}) 或 callbackName([...])，回傳內層 JSON。"""
    if not text or not callback_name:
        return None
    pattern = re.compile(r"^" + re.escape(callback_name) + r"\((.*)\)\s*$", re.DOTALL)
    m = pattern.match(text.strip())
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def is_plain_json(text: str) -> bool:
    """回應是否為純 JSON（無 callback 包裝）。"""
    t = (text or "").strip()
    return (t.startswith("{") or t.startswith("[")) and (t.endswith("}") or t.endswith("]"))


def test_version(base: str) -> tuple[bool, str]:
    """測試版本請求：GET base?callback=ver_xxx，預期 JSONP 內含 version。"""
    callback = "ver_" + str(hash(base) % 100000)
    url = base + ("&" if "?" in base else "?") + "callback=" + callback
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        text = r.text
    except requests.RequestException as e:
        return False, f"請求失敗: {e}"

    if is_plain_json(text):
        return False, (
            "GAS returns plain JSON, not JSONP (callback(JSON)). "
            "Redeploy /exec or use /dev URL."
        )

    data = parse_jsonp(text, callback)
    if data is None:
        return False, f"Response not valid JSONP, first 200 chars: {repr(text[:200])}"

    if not isinstance(data, dict):
        return False, f"Inner payload not dict: {type(data)}"

    ver = data.get("version")
    if ver is None:
        return False, f"No 'version' in response, keys: {list(data.keys())}"

    return True, f"version: {ver}"


def test_get_parse_result(base: str) -> tuple[bool, str]:
    """測試 getParseResult：GET base?action=getParseResult&token=bad&callback=xxx，預期 JSONP。"""
    callback = "parse_" + str(hash(base) % 100000)
    params = "action=getParseResult&token=bad_token&callback=" + callback
    url = base + ("&" if "?" in base else "?") + params
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        text = r.text
    except requests.RequestException as e:
        return False, f"請求失敗: {e}"

    if is_plain_json(text):
        return False, (
            "GAS returns plain JSON, not JSONP. Redeploy /exec or use /dev."
        )

    data = parse_jsonp(text, callback)
    if data is None:
        return False, f"Response not valid JSONP, first 200 chars: {repr(text[:200])}"

    if isinstance(data, dict) and data.get("error") == "NotFound":
        return True, "getParseResult JSONP OK (invalid token -> error)."
    if isinstance(data, list):
        return True, "getParseResult JSONP OK (pages array)."
    return True, f"getParseResult JSONP OK, keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"


def main() -> int:
    base_url = _get_base_url()
    if not base_url:
        print("請設定 GAS_WEBAPP_DEV_URL 或 GAS_WEBAPP_URL，或傳入 URL 作為第一個參數。")
        print("例：在 .env 寫入 GAS_WEBAPP_DEV_URL=https://script.google.com/macros/s/xxx/dev")
        print("或：python scripts/test_gas_jsonp_local.py https://script.google.com/macros/s/xxx/exec")
        return 1

    print("GAS URL:", base_url)
    print("---")

    ok1, msg1 = test_version(base_url)
    print("[版本請求]", "OK" if ok1 else "FAIL", msg1)

    ok2, msg2 = test_get_parse_result(base_url)
    print("[解析結果請求]", "OK" if ok2 else "FAIL", msg2)

    print("---")
    if ok1 and ok2:
        print("Both OK -> editor should get version and parse result (gasUrl must match this URL).")
        return 0
    print("Failed -> Redeploy GAS /exec with latest code, or use /dev URL.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
