"""
編輯器與 GAS 合約單元測試：gasUrl 解析、跨域判斷、URL 組裝。

不執行真實編輯器 JS，以 Python 對應邏輯驗證行為。
"""

import pytest
from urllib.parse import parse_qs, urlparse


def get_effective_gas_url(
    url_gas_url: str | None,
    url_token: str | None,
    url_presentation_id: str | None,
    local_storage_gas_url: str | None,
) -> str | None:
    """
    模擬編輯器 readUrlParams 後的有效 gasUrl：
    URL 有 gasUrl 則用；否則若有 token 或 presentationId 且 localStorage 有存則用 localStorage。
    """
    if url_gas_url:
        return url_gas_url.strip() or None
    if (url_token or url_presentation_id) and local_storage_gas_url:
        return local_storage_gas_url.strip() or None
    return None


def is_cross_origin(editor_origin: str, gas_url: str) -> bool:
    """模擬編輯器：gasUrl 與目前頁面不同 origin 則為跨域（需用 JSONP）。"""
    try:
        return urlparse(gas_url).netloc != urlparse(editor_origin).netloc
    except Exception:
        return True


def build_version_request_url(base_url: str, callback: str) -> str:
    """模擬編輯器 showVersion 組出的 URL：baseUrl + ?callback=xxx（或 &callback=）。"""
    base = base_url.strip()
    sep = "&" if "?" in base else "?"
    return base + sep + "callback=" + callback


def build_get_parse_result_request_url(base_url: str, token: str, callback: str) -> str:
    """模擬編輯器 loadFromToken 組出的 URL：baseUrl + action=getParseResult&token=xxx&callback=yyy。"""
    base = base_url.strip()
    sep = "&" if "?" in base else "?"
    params = "action=getParseResult&token=" + token + "&callback=" + callback
    return base + sep + params


class TestEffectiveGasUrl:
    """有效 gasUrl：URL 參數優先，其次 localStorage（當有 token 或 presentationId 時）。"""

    def test_url_gas_url_used_when_present(self) -> None:
        assert get_effective_gas_url(
            "https://script.google.com/macros/s/xxx/exec",
            "t1",
            None,
            "https://other/exec",
        ) == "https://script.google.com/macros/s/xxx/exec"

    def test_local_storage_used_when_no_url_gas_url_but_token(self) -> None:
        assert get_effective_gas_url(
            None,
            "t1",
            None,
            "https://script.google.com/macros/s/yyy/exec",
        ) == "https://script.google.com/macros/s/yyy/exec"

    def test_local_storage_used_when_no_url_gas_url_but_presentation_id(self) -> None:
        assert get_effective_gas_url(
            None,
            None,
            "pres123",
            "https://script.google.com/macros/s/zzz/exec",
        ) == "https://script.google.com/macros/s/zzz/exec"

    def test_none_when_no_url_and_no_local_storage(self) -> None:
        assert get_effective_gas_url(None, "t1", None, None) is None
        assert get_effective_gas_url("", "t1", None, "") is None


class TestCrossOrigin:
    """跨域判斷：編輯器與 GAS 不同 origin 時應使用 JSONP。"""

    def test_different_origin_is_cross(self) -> None:
        assert is_cross_origin("https://poro-ai.github.io", "https://script.google.com/macros/s/x/exec") is True

    def test_same_origin_not_cross(self) -> None:
        assert is_cross_origin("https://script.google.com", "https://script.google.com/macros/s/x/exec") is False

    def test_same_host_different_path_still_same_origin(self) -> None:
        assert is_cross_origin("https://example.com", "https://example.com/gas/exec") is False


class TestEditorRequestUrls:
    """編輯器組出的請求 URL 格式（與 GAS doGet 參數一致）。"""

    def test_version_url_has_callback_param(self) -> None:
        url = build_version_request_url("https://script.google.com/macros/s/id/exec", "obe_ver_123")
        assert "callback=obe_ver_123" in url
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        assert "callback" in qs
        assert qs["callback"] == ["obe_ver_123"]

    def test_get_parse_result_url_has_action_token_callback(self) -> None:
        url = build_get_parse_result_request_url(
            "https://script.google.com/macros/s/id/exec",
            "abc123",
            "obe_parse_456",
        )
        assert "action=getParseResult" in url
        assert "token=abc123" in url
        assert "callback=obe_parse_456" in url
        qs = parse_qs(urlparse(url).query)
        assert qs.get("action") == ["getParseResult"]
        assert qs.get("token") == ["abc123"]
        assert qs.get("callback") == ["obe_parse_456"]
