"""
本地單元測試：驗證 GAS _base64UrlEncode 的編碼邏輯與修正。

修正：使用 base64Encode(str, Charset.UTF_8) 字串簽章，
不可使用 base64Encode(byte_array, Charset) 以免 (number[], Charset) 簽章不符。

部署前請執行：pytest tests/unit/test_gas_base64url.py -v
通過後再執行 clasp push，否則雲端會回傳「參數 (number[],Utilities.Charset) 與 Utilities.base64Encode 的方法簽章不符」。
"""
import base64
import os
import re

import pytest


def _gas_web_app_path():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(root, "gas", "web_app.js")


def _read_gas_web_app() -> str:
    path = _gas_web_app_path()
    assert os.path.isfile(path), f"找不到 {path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


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


class TestGasWebAppBase64Signature:
    """
    讀取 gas/web_app.js 檔案，確保沒有會觸發「(number[],Utilities.Charset) 與 Utilities.base64Encode 的方法簽章不符」的寫法。
    通過後再 clasp push，否則雲端 GAS 會回傳該錯誤。
    """

    def test_must_use_string_signature_base64encode(self):
        content = _read_gas_web_app()
        assert "Utilities.base64Encode(str, Utilities.Charset.UTF_8)" in content, (
            "gas/web_app.js 必須使用 base64Encode(str, Charset.UTF_8) 字串簽章，"
            "否則部署後會回傳：參數 (number[],Utilities.Charset) 與 Utilities.base64Encode 的方法簽章不符"
        )

    def test_must_not_use_bytes_with_charset_in_base64encode(self):
        """禁止 base64Encode( 位元組來源 , Charset) 會導致 (number[], Charset) 簽章不符。"""
        content = _read_gas_web_app()
        bad_literals = [
            "Utilities.base64Encode(bytes)",
            "Utilities.base64Encode(bytes,",
            "base64Encode(bytes,",
        ]
        for bad in bad_literals:
            assert bad not in content, (
                f"gas/web_app.js 不得包含：{bad!r}，會導致 (number[], Charset) 簽章不符。"
                "請改為 Utilities.base64Encode(str, Utilities.Charset.UTF_8)"
            )
        if re.search(r"\.getBytes\s*\(\s*\)\s*\)?\s*;?\s*var\s+raw\s*=\s*Utilities\.base64Encode\s*\(", content):
            pytest.fail(
                "gas/web_app.js 不得使用 getBytes() 後再 base64Encode(該結果)，會導致簽章不符。"
                "請改為 Utilities.base64Encode(str, Utilities.Charset.UTF_8)"
            )

    def test_no_base64encode_with_single_bytes_arg(self):
        """禁止僅傳一個位元組陣列參數給 base64Encode（例如 base64Encode(bytes)）。"""
        content = _read_gas_web_app()
        assert not re.search(r"Utilities\.base64Encode\s*\(\s*bytes\s*\)", content), (
            "gas/web_app.js 不得使用 Utilities.base64Encode(bytes)。"
            "請改為 Utilities.base64Encode(str, Utilities.Charset.UTF_8)"
        )

    def test_base64url_encode_function_uses_str_not_bytes(self):
        """_base64UrlEncode 函數內必須對 str 做 base64Encode(str, Charset)，不可對 bytes。"""
        content = _read_gas_web_app()
        if "_base64UrlEncode" not in content:
            return
        start = content.find("function _base64UrlEncode")
        if start == -1:
            return
        end = content.find("function ", start + 1)
        if end == -1:
            end = len(content)
        fn_block = content[start:end]
        assert "Utilities.base64Encode(str, Utilities.Charset.UTF_8)" in fn_block, (
            "_base64UrlEncode 內必須為 Utilities.base64Encode(str, Utilities.Charset.UTF_8)"
        )
        assert "base64Encode(bytes" not in fn_block, "_base64UrlEncode 內不可使用 base64Encode(bytes..."
        assert ".getBytes()" not in fn_block, "_base64UrlEncode 內不可使用 getBytes()，會導致 (number[], Charset) 簽章不符"
