"""
本地單元測試：驗證 GAS _base64UrlEncode 的編碼邏輯與修正。

修正：使用 base64Encode(str, Charset.UTF_8) 字串簽章，
不可使用 base64Encode(byte_array, Charset) 以免 (number[], Charset) 簽章不符。
"""
import base64
import re

import pytest


def base64url_encode_string(s: str) -> str:
    """
    等同 GAS：Utilities.base64Encode(str, Utilities.Charset.UTF_8) 再做 base64url 替換。
    使用字串 + UTF-8 簽章，避免 (byte_array, Charset) 簽章錯誤。
    """
    raw = base64.b64encode(s.encode("utf-8")).decode("ascii")
    return raw.replace("+", "-").replace("/", "_").rstrip("=")


class TestBase64UrlEncode:
    """驗證 base64url 編碼邏輯（與 GAS _base64UrlEncode 一致）。"""

    def test_encode_empty_string(self):
        assert base64url_encode_string("") == ""

    def test_encode_json_header(self):
        s = '{"alg":"RS256","typ":"JWT"}'
        out = base64url_encode_string(s)
        assert "+" not in out and "/" not in out
        assert out.endswith("JWT") or len(out) > 0

    def test_encode_json_payload(self):
        s = '{"iss":"test@example.iam.gserviceaccount.com","aud":"https://oauth2.googleapis.com/token"}'
        out = base64url_encode_string(s)
        assert "=" not in out.rstrip("=")
        assert re.match(r"^[A-Za-z0-9_-]+$", out)

    def test_roundtrip_not_applicable(self):
        """base64url 用於 JWT，此處僅確認編碼輸出格式正確。"""
        s = "hello"
        out = base64url_encode_string(s)
        assert len(out) > 0 and " " not in out


def test_gas_web_app_uses_string_signature():
    """確保 gas/web_app.js 使用 base64Encode(str, Charset.UTF_8)，避免 (number[], Charset) 簽章不符。"""
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "gas", "web_app.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Utilities.base64Encode(str, Utilities.Charset.UTF_8)" in content, (
        "應使用 base64Encode(str, Charset.UTF_8) 字串簽章，避免 (number[], Charset) 不符"
    )
    assert "Utilities.base64Encode(bytes)" not in content, (
        "不可使用 base64Encode(bytes)，會導致方法簽章不符"
    )
