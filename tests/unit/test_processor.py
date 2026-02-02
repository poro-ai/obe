"""PDFProcessor 單元測試：parse_from_gcs 編排（mock GCSClient + GeminiFileClient）。"""

import pytest
from unittest.mock import MagicMock, patch

from src.clients.gcs_client import GCSClient
from src.clients.gemini_client import GeminiFileClient
from src.models.schema import BlockElement, PageBlock
from src.services.processor import PDFProcessor, _fill_image_content


@pytest.fixture
def mock_gcs() -> MagicMock:
    gcs = MagicMock(spec=GCSClient)
    gcs.read_blob_bytes.return_value = b"fake pdf bytes"
    return gcs


@pytest.fixture
def mock_gemini() -> MagicMock:
    gemini = MagicMock(spec=GeminiFileClient)
    gemini.upload_bytes.return_value = "https://generativelanguage.googleapis.com/v1beta/files/abc"
    gemini.parse_pdf_structured.return_value = [
        PageBlock(page=1, elements=[BlockElement(type="text", content="hi", description="")]),
    ]
    return gemini


def test_parse_from_gcs_calls_gcs_then_gemini_then_parse(
    mock_gcs: MagicMock,
    mock_gemini: MagicMock,
) -> None:
    """parse_from_gcs 應依序：讀 GCS → upload_bytes → parse_pdf_structured，回傳 PageBlock 列表。"""
    processor = PDFProcessor(gcs_client=mock_gcs, gemini_client=mock_gemini)
    result = processor.parse_from_gcs("uploads/123/file.pdf")
    mock_gcs.read_blob_bytes.assert_called_once_with("uploads/123/file.pdf")
    mock_gemini.upload_bytes.assert_called_once()
    call_kw = mock_gemini.upload_bytes.call_args[1]
    assert call_kw["data"] == b"fake pdf bytes"
    assert call_kw["display_name"] == "file.pdf"
    assert call_kw["mime_type"] == "application/pdf"
    mock_gemini.parse_pdf_structured.assert_called_once()
    assert len(result) == 1
    assert result[0].page == 1
    assert result[0].elements[0].content == "hi"


def test_parse_from_gcs_with_bucket_name_creates_new_gcs(
    mock_gcs: MagicMock,
    mock_gemini: MagicMock,
) -> None:
    """傳入 bucket_name 時應以該 bucket 讀取（此處僅驗證仍會呼叫 read_blob_bytes）。"""
    processor = PDFProcessor(gcs_client=mock_gcs, gemini_client=mock_gemini)
    with patch("src.services.processor.GCSClient") as MockGCS:
        mock_new_gcs = MagicMock()
        mock_new_gcs.read_blob_bytes.return_value = b"other bytes"
        MockGCS.return_value = mock_new_gcs
        processor.parse_from_gcs("path/doc.pdf", bucket_name="other-bucket")
    MockGCS.assert_called_once_with("other-bucket")
    mock_new_gcs.read_blob_bytes.assert_called_once_with("path/doc.pdf")


def test_parse_from_gcs_display_name_from_blob_path(
    mock_gcs: MagicMock,
    mock_gemini: MagicMock,
) -> None:
    """display_name 應從 blob_path 最後一段取得，空則 'document.pdf'。"""
    processor = PDFProcessor(gcs_client=mock_gcs, gemini_client=mock_gemini)
    processor.parse_from_gcs("uploads/2024/01/report.pdf")
    call_kw = mock_gemini.upload_bytes.call_args[1]
    assert call_kw["display_name"] == "report.pdf"


def test_parse_from_gcs_gemini_raises_propagates(
    mock_gcs: MagicMock,
    mock_gemini: MagicMock,
) -> None:
    """Gemini 拋出例外時應向上拋出。"""
    mock_gemini.upload_bytes.side_effect = TimeoutError("timeout")
    processor = PDFProcessor(gcs_client=mock_gcs, gemini_client=mock_gemini)
    with pytest.raises(TimeoutError):
        processor.parse_from_gcs("x.pdf")


def test_fill_image_content_fills_empty_image_elements() -> None:
    """_fill_image_content 應將 type=image 且 content 為空的區塊填入 data URI。"""
    blocks = [
        PageBlock(
            page=1,
            elements=[
                BlockElement(type="image", content="", description="圖1"),
                BlockElement(type="text", content="hi", description=""),
                BlockElement(type="image", content="", description="圖2"),
            ],
        ),
    ]
    images_by_page = {
        0: [
            ("base64img1", "image/png"),
            ("base64img2", "image/jpeg"),
        ],
    }
    result = _fill_image_content(blocks, images_by_page)
    assert len(result) == 1
    assert result[0].page == 1
    assert result[0].elements[0].type == "image"
    assert result[0].elements[0].content == "data:image/png;base64,base64img1"
    assert result[0].elements[0].description == "圖1"
    assert result[0].elements[1].content == "hi"
    assert result[0].elements[2].type == "image"
    assert result[0].elements[2].content == "data:image/jpeg;base64,base64img2"


def test_fill_image_content_skips_when_no_images_for_page() -> None:
    """_fill_image_content 無該頁圖片時不改動 content。"""
    blocks = [
        PageBlock(
            page=1,
            elements=[BlockElement(type="image", content="", description="圖")],
        ),
    ]
    result = _fill_image_content(blocks, {})
    assert result[0].elements[0].content == ""
