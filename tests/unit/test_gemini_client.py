"""GeminiFileClient 單元測試（Mock）。"""

import pytest
from unittest.mock import MagicMock, patch

from src.clients.gemini_client import GeminiFileClient
from src.models.schema import PageExtract


@pytest.fixture
def gemini_client() -> GeminiFileClient:
    """建立受測的 GeminiFileClient，API key 以 Mock 取代實際呼叫。"""
    with patch("src.clients.gemini_client.genai"):
        return GeminiFileClient(api_key="test-key")


@pytest.fixture
def mock_upload_file():
    """Mock genai.upload_file 回傳的檔案物件。"""
    with patch("src.clients.gemini_client.genai.upload_file") as m:
        fake_file = MagicMock()
        fake_file.name = "files/abc123"
        m.return_value = fake_file
        yield m


@pytest.fixture
def mock_get_file_active():
    """Mock genai.get_file 使檔案狀態為 ACTIVE。"""
    with patch("src.clients.gemini_client.genai.get_file") as m:
        state = MagicMock()
        state.name = "ACTIVE"
        file_obj = MagicMock()
        file_obj.state = state
        m.return_value = file_obj
        yield m


def test_upload_file_returns_uri_when_ready(
    gemini_client: GeminiFileClient,
    mock_upload_file: MagicMock,
    mock_get_file_active: MagicMock,
    tmp_path,
) -> None:
    """上傳檔案後輪詢到 ACTIVE，應回傳 file URI。"""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 dummy")

    uri = gemini_client.upload_file(pdf_path, mime_type="application/pdf")

    assert "generativelanguage.googleapis.com" in uri or "files/" in uri
    mock_upload_file.assert_called_once()
    mock_get_file_active.assert_called()


def test_upload_file_raises_when_file_not_found(gemini_client: GeminiFileClient) -> None:
    """若檔案不存在，upload_file 應拋出 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError, match="File not found"):
        gemini_client.upload_file("/nonexistent/path.pdf")


def test_parse_response_to_page_extracts_returns_list(gemini_client: GeminiFileClient) -> None:
    """_parse_response_to_page_extracts 將 JSON 列表轉成 PageExtract 列表。"""
    mock_response = MagicMock()
    mock_response.text = '[{"group_id": "g1", "visual_summary": "fig", "associated_text": "txt", "page_number": 1}]'

    result = gemini_client._parse_response_to_page_extracts(mock_response)

    assert len(result) == 1
    assert isinstance(result[0], PageExtract)
    assert result[0].group_id == "g1"
    assert result[0].page_number == 1
