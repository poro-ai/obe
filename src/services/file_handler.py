"""大型檔案處理服務：整合 Gemini File API 上傳、輪詢與重試，供 DocumentProcessor 取得 file_uri。"""

import logging
import time
from pathlib import Path
from typing import BinaryIO

from src.clients.gemini_client import GeminiFileClient

logger = logging.getLogger(__name__)

# 可重試的例外（網路超時、Gemini 處理暫時失敗等）
RETRYABLE_EXCEPTIONS = (TimeoutError, RuntimeError, ConnectionError, OSError)


class FileHandler:
    """
    處理大型檔案（如 150MB PDF）上傳至 Gemini File API 的服務層。
    - File API 整合：透過 GeminiFileClient.upload_file / upload_bytes 上傳。
    - 狀態監控：Client 內建輪詢 (Polling)，等待檔案狀態從 PROCESSING 變更為 ACTIVE。
    - 異常處理：對 150MB 可能產生的網路超時或 Gemini 處理失敗，實作 try-except 與指數退避重試。
    - 組件複用：可接受從 GCSClient 傳來的檔案流（bytes 或 BinaryIO），回傳 file_uri 供 DocumentProcessor 使用。
    """

    def __init__(
        self,
        gemini_client: GeminiFileClient,
        max_retries: int = 3,
        retry_backoff_seconds: float = 5.0,
    ) -> None:
        self._gemini = gemini_client
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff_seconds

    def upload_to_gemini(
        self,
        file_path: str | Path,
        mime_type: str = "application/pdf",
    ) -> str:
        """
        使用 Gemini File API 上傳本機檔案，並輪詢直到狀態為 ACTIVE。
        含重試機制，適用於 150MB 可能產生的網路超時或處理失敗。
        回傳 file_uri 供 DocumentProcessor 使用。
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        last_error: BaseException | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                file_uri = self._gemini.upload_file(path=str(path), mime_type=mime_type)
                logger.info("upload_to_gemini succeeded on attempt %s: %s", attempt, path.name)
                return file_uri
            except RETRYABLE_EXCEPTIONS as e:
                last_error = e
                logger.warning(
                    "upload_to_gemini attempt %s/%s failed: %s",
                    attempt,
                    self._max_retries,
                    e,
                )
                if attempt == self._max_retries:
                    raise last_error
                delay = self._retry_backoff * (2 ** (attempt - 1))
                time.sleep(delay)

    def upload_from_stream(
        self,
        data: bytes | BinaryIO,
        display_name: str,
        mime_type: str = "application/pdf",
    ) -> str:
        """
        接受從 GCSClient 傳來的檔案流（bytes 或 BinaryIO），上傳至 Gemini File API。
        輪詢直到狀態為 ACTIVE，含重試。回傳 file_uri 供 DocumentProcessor 使用。
        """
        if hasattr(data, "read"):
            data = data.read()
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes or file-like with .read()")

        last_error: BaseException | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                file_uri = self._gemini.upload_bytes(
                    data=data,
                    display_name=display_name,
                    mime_type=mime_type,
                )
                logger.info(
                    "upload_from_stream succeeded on attempt %s: %s",
                    attempt,
                    display_name,
                )
                return file_uri
            except RETRYABLE_EXCEPTIONS as e:
                last_error = e
                logger.warning(
                    "upload_from_stream attempt %s/%s failed: %s",
                    attempt,
                    self._max_retries,
                    e,
                )
                if attempt == self._max_retries:
                    raise last_error
                delay = self._retry_backoff * (2 ** (attempt - 1))
                time.sleep(delay)
