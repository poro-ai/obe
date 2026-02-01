"""FileHandler 單元測試：upload_to_gemini、upload_from_stream，mock GeminiFileClient。"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.clients.gemini_client import GeminiFileClient
from src.services.file_handler import FileHandler, RETRYABLE_EXCEPTIONS


@pytest.fixture
def mock_gemini() -> MagicMock:
    gemini = MagicMock(spec=GeminiFileClient)
    gemini.upload_file.return_value = "https://generativelanguage.googleapis.com/v1beta/files/f1"
    gemini.upload_bytes.return_value = "https://generativelanguage.googleapis.com/v1beta/files/f2"
    return gemini


@pytest.fixture
def file_handler(mock_gemini: MagicMock) -> FileHandler:
    return FileHandler(gemini_client=mock_gemini, max_retries=3, retry_backoff_seconds=0.01)


def test_upload_to_gemini_success(
    file_handler: FileHandler,
    mock_gemini: MagicMock,
    tmp_path: Path,
) -> None:
    """upload_to_gemini 成功時應回傳 file_uri。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"pdf")
    uri = file_handler.upload_to_gemini(str(pdf), mime_type="application/pdf")
    assert uri == "https://generativelanguage.googleapis.com/v1beta/files/f1"
    mock_gemini.upload_file.assert_called_once_with(path=str(pdf), mime_type="application/pdf")


def test_upload_to_gemini_file_not_found_raises(file_handler: FileHandler) -> None:
    """upload_to_gemini 若檔案不存在應拋 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError, match="File not found"):
        file_handler.upload_to_gemini("/nonexistent/file.pdf")


def test_upload_to_gemini_retries_on_timeout(
    mock_gemini: MagicMock,
    tmp_path: Path,
) -> None:
    """upload_to_gemini 在 RETRYABLE_EXCEPTIONS 時應重試，成功後回傳。"""
    mock_gemini.upload_file.side_effect = [TimeoutError("timeout"), "https://files/ok"]
    handler = FileHandler(gemini_client=mock_gemini, max_retries=3, retry_backoff_seconds=0.01)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"x")
    uri = handler.upload_to_gemini(str(pdf))
    assert uri == "https://files/ok"
    assert mock_gemini.upload_file.call_count == 2


def test_upload_to_gemini_raises_after_max_retries(
    mock_gemini: MagicMock,
    tmp_path: Path,
) -> None:
    """upload_to_gemini 重試用盡後應拋出最後一次例外。"""
    mock_gemini.upload_file.side_effect = TimeoutError("timeout")
    handler = FileHandler(gemini_client=mock_gemini, max_retries=2, retry_backoff_seconds=0.01)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"x")
    with pytest.raises(TimeoutError, match="timeout"):
        handler.upload_to_gemini(str(pdf))
    assert mock_gemini.upload_file.call_count == 2


def test_upload_from_stream_bytes_success(
    file_handler: FileHandler,
    mock_gemini: MagicMock,
) -> None:
    """upload_from_stream 接受 bytes 時應呼叫 upload_bytes 並回傳 file_uri。"""
    data = b"pdf content"
    uri = file_handler.upload_from_stream(data, display_name="doc.pdf", mime_type="application/pdf")
    assert uri == "https://generativelanguage.googleapis.com/v1beta/files/f2"
    mock_gemini.upload_bytes.assert_called_once_with(
        data=data,
        display_name="doc.pdf",
        mime_type="application/pdf",
    )


def test_upload_from_stream_binary_io_reads_then_uploads(
    file_handler: FileHandler,
    mock_gemini: MagicMock,
) -> None:
    """upload_from_stream 接受 BinaryIO 時應 read() 後再上傳。"""
    from io import BytesIO
    data = BytesIO(b"streamed pdf")
    uri = file_handler.upload_from_stream(data, display_name="s.pdf")
    call_data = mock_gemini.upload_bytes.call_args[1]["data"]
    assert call_data == b"streamed pdf"


def test_upload_from_stream_retries_on_connection_error(
    mock_gemini: MagicMock,
) -> None:
    """upload_from_stream 在 RETRYABLE_EXCEPTIONS 時應重試。"""
    mock_gemini.upload_bytes.side_effect = [ConnectionError("conn"), "https://files/ok"]
    handler = FileHandler(gemini_client=mock_gemini, max_retries=3, retry_backoff_seconds=0.01)
    uri = handler.upload_from_stream(b"x", display_name="d.pdf")
    assert uri == "https://files/ok"
    assert mock_gemini.upload_bytes.call_count == 2


def test_upload_from_stream_invalid_type_raises(file_handler: FileHandler) -> None:
    """upload_from_stream 若 data 非 bytes 且無 read() 應拋 TypeError。"""
    with pytest.raises(TypeError, match="data must be bytes"):
        file_handler.upload_from_stream("not bytes", display_name="x.pdf")  # type: ignore[arg-type]
