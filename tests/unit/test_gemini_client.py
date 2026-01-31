"""
GeminiFileClient 單元測試（Mock）。

不需部署到 GCF 即可在本機驗證 PDF 解析流程：
  pytest tests/unit/test_gemini_client.py -v
通過後再 deploy，可減少「部署後才發現 API 用法錯誤」的次數。
"""

import pytest
from unittest.mock import MagicMock, patch

from src.clients.gemini_client import GeminiFileClient
from src.models.schema import BlockElement, PageBlock, PageExtract


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


# ----- parse_pdf_with_file_uri：驗證「file_uri → get_file → generate_content」流程，不需 deploy -----


def test_parse_pdf_with_file_uri_extracts_file_name_and_calls_get_file_and_generate_content(
    gemini_client: GeminiFileClient,
) -> None:
    """parse_pdf_with_file_uri 應從 file_uri 取出 file_name，呼叫 genai.get_file，再以 [prompt, file_obj] 呼叫 generate_content。"""
    file_uri = "https://generativelanguage.googleapis.com/v1beta/files/xyz789"
    mock_file_obj = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '[{"group_id": "p1", "visual_summary": "s", "associated_text": "t", "page_number": 1}]'

    with patch("src.clients.gemini_client.genai.get_file", return_value=mock_file_obj) as mock_get_file:
        with patch.object(gemini_client._model, "generate_content", return_value=mock_response) as mock_gen:
            result = gemini_client.parse_pdf_with_file_uri(file_uri)

    mock_get_file.assert_called_once_with("files/xyz789")
    mock_gen.assert_called_once()
    call_args = mock_gen.call_args[0][0]
    assert isinstance(call_args, list)
    assert len(call_args) == 2
    assert "PDF" in call_args[0]
    assert call_args[1] is mock_file_obj
    assert len(result) == 1
    assert result[0].group_id == "p1"
    assert result[0].page_number == 1


def test_parse_pdf_with_file_uri_raises_on_invalid_uri(gemini_client: GeminiFileClient) -> None:
    """無效的 file_uri（取不出 file_name）應拋出 ValueError。"""
    with pytest.raises(ValueError, match="Invalid file_uri"):
        gemini_client.parse_pdf_with_file_uri("https://generativelanguage.googleapis.com/v1beta/")


def test_parse_pdf_with_file_uri_handles_pages_dict(gemini_client: GeminiFileClient) -> None:
    """generate_content 回傳的 JSON 若為 { pages: [...] }，應正確解析。"""
    file_uri = "https://generativelanguage.googleapis.com/v1beta/files/abc"
    mock_response = MagicMock()
    mock_response.text = '{"pages": [{"group_id": "g2", "visual_summary": "v", "associated_text": "a", "page_number": 2}]}'

    with patch("src.clients.gemini_client.genai.get_file", return_value=MagicMock()):
        with patch.object(gemini_client._model, "generate_content", return_value=mock_response):
            result = gemini_client.parse_pdf_with_file_uri(file_uri)

    assert len(result) == 1
    assert result[0].group_id == "g2"
    assert result[0].page_number == 2


def test_upload_bytes_writes_temp_file_and_calls_upload_file(
    gemini_client: GeminiFileClient,
    mock_upload_file: MagicMock,
    mock_get_file_active: MagicMock,
) -> None:
    """upload_bytes 應寫入暫存檔後呼叫 upload_file(path=...)，回傳 file URI。"""
    data = b"%PDF-1.4 minimal"
    uri = gemini_client.upload_bytes(data, display_name="test.pdf", mime_type="application/pdf")

    assert mock_upload_file.called
    call_kw = mock_upload_file.call_args[1]
    assert call_kw.get("mime_type") == "application/pdf"
    assert "generativelanguage.googleapis.com" in uri or "files/" in uri


def test_parse_response_to_page_blocks_returns_page_blocks(gemini_client: GeminiFileClient) -> None:
    """_parse_response_to_page_blocks 將 JSON 陣列轉成 PageBlock 列表。"""
    mock_response = MagicMock()
    mock_response.text = '[{"page": 1, "elements": [{"type": "image", "content": "", "description": "圖"}, {"type": "text", "content": "內文", "description": ""}]}]'

    result = gemini_client._parse_response_to_page_blocks(mock_response)

    assert len(result) == 1
    assert isinstance(result[0], PageBlock)
    assert result[0].page == 1
    assert len(result[0].elements) == 2
    assert result[0].elements[0].type == "image"
    assert result[0].elements[0].description == "圖"
    assert result[0].elements[1].type == "text"
    assert result[0].elements[1].content == "內文"
