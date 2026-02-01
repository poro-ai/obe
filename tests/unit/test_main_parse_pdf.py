"""main.parse_pdf 單元測試：請求驗證、回傳格式，mock PDFProcessor 與 jsonify。"""

import pytest
from unittest.mock import MagicMock, patch

from src.models.schema import BlockElement, PageBlock


def _fake_jsonify(obj: dict) -> MagicMock:
    """取代 jsonify，避免需要 Flask app context；回傳物件的 get_json() 為傳入的 dict。"""
    m = MagicMock()
    m.get_json.return_value = obj
    return m


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock GCSClient、GeminiFileClient、PDFProcessor、jsonify，避免實際 I/O 與 app context。"""
    with (
        patch("main.GCSClient"),
        patch("main.GeminiFileClient"),
        patch("main.PDFProcessor") as MockProcessor,
        patch("main.jsonify", side_effect=_fake_jsonify),
    ):
        mock_instance = MagicMock()
        mock_instance.parse_from_gcs.return_value = [
            PageBlock(page=1, elements=[BlockElement(type="text", content="hi", description="")]),
        ]
        MockProcessor.return_value = mock_instance
        yield MockProcessor


def _request(method: str, json_body: dict | None = None) -> MagicMock:
    req = MagicMock()
    req.method = method
    req.get_json = MagicMock(return_value=json_body if json_body is not None else {})
    return req


def test_parse_pdf_get_returns_405() -> None:
    """GET 請求應回傳 405 Method not allowed。"""
    import main
    req = _request("GET")
    response, status_code = main.parse_pdf(req)
    assert status_code == 405
    assert response.get_json()["error"] == "Method not allowed"


def test_parse_pdf_post_missing_bucket_returns_400() -> None:
    """POST 缺 bucket 應回傳 400。"""
    import main
    req = _request("POST", {"blob_path": "path/file.pdf"})
    response, status_code = main.parse_pdf(req)
    assert status_code == 400
    assert response.get_json()["error"] == "Missing bucket or blob_path"


def test_parse_pdf_post_missing_blob_path_returns_400() -> None:
    """POST 缺 blob_path 應回傳 400。"""
    import main
    req = _request("POST", {"bucket": "my-bucket"})
    response, status_code = main.parse_pdf(req)
    assert status_code == 400
    assert response.get_json()["error"] == "Missing bucket or blob_path"


def test_parse_pdf_post_empty_body_returns_400() -> None:
    """POST 空 body 應回傳 400。"""
    import main
    req = _request("POST", {})
    response, status_code = main.parse_pdf(req)
    assert status_code == 400


def test_parse_pdf_post_valid_returns_200_and_pages(mock_dependencies: MagicMock) -> None:
    """POST 含 bucket、blob_path 且 processor 成功時應回傳 200 與 success、count、pages。"""
    import main
    req = _request("POST", {"bucket": "obe-files", "blob_path": "uploads/x.pdf"})
    response, status_code = main.parse_pdf(req)
    assert status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] == 1
    assert len(data["pages"]) == 1
    assert data["pages"][0]["page"] == 1
    assert data["pages"][0]["elements"][0]["content"] == "hi"
    mock_dependencies.return_value.parse_from_gcs.assert_called_once_with(
        "uploads/x.pdf",
        bucket_name="obe-files",
    )


def test_parse_pdf_post_processor_raises_non_retryable_returns_500(mock_dependencies: MagicMock) -> None:
    """processor 拋出非 RETRYABLE 例外時應立即回傳 500。"""
    import main
    mock_dependencies.return_value.parse_from_gcs.side_effect = ValueError("bad input")
    req = _request("POST", {"bucket": "b", "blob_path": "p.pdf"})
    response, status_code = main.parse_pdf(req)
    assert status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "bad input" in data["error"]


def test_parse_pdf_post_processor_retryable_returns_500_after_retries(mock_dependencies: MagicMock) -> None:
    """processor 連續拋 RETRYABLE 時重試用盡後回傳 500。"""
    import main
    mock_dependencies.return_value.parse_from_gcs.side_effect = TimeoutError("timeout")
    req = _request("POST", {"bucket": "b", "blob_path": "p.pdf"})
    response, status_code = main.parse_pdf(req)
    assert status_code == 500
    assert response.get_json()["success"] is False
    assert "timeout" in response.get_json()["error"]
    assert mock_dependencies.return_value.parse_from_gcs.call_count == 2  # PARSE_MAX_RETRIES
