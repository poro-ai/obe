"""GCSClient 單元測試：read_blob_bytes、get_blob_uri，以 mock 取代實際 GCS。"""

import pytest
from unittest.mock import MagicMock, patch

from src.clients.gcs_client import GCSClient


@pytest.fixture
def mock_storage_client() -> MagicMock:
    """Mock google.cloud.storage.Client 與 bucket/blob 鏈。"""
    with patch("src.clients.gcs_client.storage") as mock_storage:
        mock_client = MagicMock()
        mock_storage.Client.return_value = mock_client
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_bytes.return_value = b"pdf content"
        yield mock_client, mock_bucket, mock_blob


def test_read_blob_bytes_returns_bytes(
    mock_storage_client: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """read_blob_bytes 應呼叫 bucket(名稱).blob(路徑).download_as_bytes() 並回傳 bytes。"""
    _client, _bucket, mock_blob = mock_storage_client
    mock_blob.download_as_bytes.return_value = b"file content"
    client = GCSClient(bucket_name="my-bucket")
    result = client.read_blob_bytes("path/to/file.pdf")
    assert result == b"file content"
    _client.bucket.assert_called_once_with("my-bucket")
    _bucket.blob.assert_called_once_with("path/to/file.pdf")
    mock_blob.download_as_bytes.assert_called_once()


def test_get_blob_uri_returns_gs_uri() -> None:
    """get_blob_uri 應回傳 gs://bucket/path 格式。"""
    with patch("src.clients.gcs_client.storage"):
        client = GCSClient(bucket_name="obe-files")
        uri = client.get_blob_uri("uploads/123/doc.pdf")
    assert uri == "gs://obe-files/uploads/123/doc.pdf"


def test_get_blob_uri_no_download(
    mock_storage_client: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """get_blob_uri 不應呼叫 download，僅組 URI。"""
    _client, _bucket, mock_blob = mock_storage_client
    with patch("src.clients.gcs_client.storage"):
        client = GCSClient(bucket_name="b")
        client.get_blob_uri("p/file.pdf")
    mock_blob.download_as_bytes.assert_not_called()


def test_init_uses_bucket_name(
    mock_storage_client: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """建構時傳入的 bucket_name 應被用於 read_blob_bytes。"""
    _client, _bucket, _blob = mock_storage_client
    client = GCSClient(bucket_name="custom-bucket")
    client.read_blob_bytes("x.pdf")
    _client.bucket.assert_called_once_with("custom-bucket")
