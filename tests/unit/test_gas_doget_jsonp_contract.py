"""
GAS doGet JSONP 合約單元測試：驗證版本與 getParseResult 的 JSONP 回應格式。

不呼叫真實 GAS，僅測試預期之回應格式（與 editor 端解析邏輯一致）。
"""

import json
import re
import pytest

# 模擬 GAS doGet 回傳的 JSONP 格式（與 web_app.js 一致）
BACKEND_VERSION = "1.0.06"


def build_version_jsonp(callback: str) -> str:
    """模擬 doGet 預設（版本）回應：callback(JSON)。"""
    payload = {
        "message": "Success",
        "params": {},
        "version": BACKEND_VERSION,
    }
    return callback + "(" + json.dumps(payload) + ")"


def build_get_parse_result_jsonp(callback: str, data: list | dict | None) -> str:
    """模擬 doGet action=getParseResult 回應：callback(JSON)。"""
    body = data if data is not None else {"error": "NotFound", "message": "Token expired or invalid"}
    return callback + "(" + json.dumps(body) + ")"


def parse_jsonp_response(text: str, callback_name: str) -> dict | list:
    """
    解析 JSONP 回應：預期格式為 callbackName({...}) 或 callbackName([...])。
    回傳內層的 JSON 物件或陣列。
    """
    pattern = re.compile(r"^" + re.escape(callback_name) + r"\((.*)\)\s*$", re.DOTALL)
    m = pattern.match(text)
    if not m:
        raise ValueError("Not valid JSONP format")
    return json.loads(m.group(1))


class TestVersionJsonpContract:
    """版本 JSONP：編輯器以 callback 取版本時，GAS 回傳 callback({version: ...})。"""

    def test_build_version_jsonp_is_valid_js(self) -> None:
        text = build_version_jsonp("obe_ver_123")
        assert text.startswith("obe_ver_123(")
        assert text.endswith(")")
        inner = text[len("obe_ver_123(") : -1]
        data = json.loads(inner)
        assert data["version"] == BACKEND_VERSION

    def test_parse_version_jsonp_returns_version(self) -> None:
        callback = "obe_ver_123"
        text = build_version_jsonp(callback)
        data = parse_jsonp_response(text, callback)
        assert isinstance(data, dict)
        assert data.get("version") == BACKEND_VERSION

    def test_version_payload_has_version_key(self) -> None:
        payload = {"message": "Success", "params": {}, "version": BACKEND_VERSION}
        text = "cb(" + json.dumps(payload) + ")"
        parsed = parse_jsonp_response(text, "cb")
        assert "version" in parsed
        assert parsed["version"] == BACKEND_VERSION


class TestGetParseResultJsonpContract:
    """getParseResult JSONP：編輯器以 callback 取解析結果時，GAS 回傳 callback(pages 陣列或 error)。"""

    def test_build_get_parse_result_success_jsonp(self) -> None:
        pages = [{"page": 1, "elements": [{"type": "text", "content": "hi", "description": ""}]}]
        text = build_get_parse_result_jsonp("obe_parse_456", pages)
        assert "obe_parse_456(" in text
        parsed = parse_jsonp_response(text, "obe_parse_456")
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["page"] == 1

    def test_build_get_parse_result_error_jsonp(self) -> None:
        text = build_get_parse_result_jsonp("obe_parse_789", None)
        parsed = parse_jsonp_response(text, "obe_parse_789")
        assert isinstance(parsed, dict)
        assert parsed.get("error") == "NotFound"

    def test_parse_result_payload_either_pages_or_error(self) -> None:
        success = build_get_parse_result_jsonp("cb", [{"page": 1, "elements": []}])
        p_success = parse_jsonp_response(success, "cb")
        assert isinstance(p_success, list)
        err = build_get_parse_result_jsonp("cb", None)
        p_err = parse_jsonp_response(err, "cb")
        assert isinstance(p_err, dict)
        assert "error" in p_err
