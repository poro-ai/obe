"""
PDF 結構化解析處理器：GCS 讀取 → Gemini File API 上傳（含狀態輪詢）→ 結構化解析。

- Gemini File API 整合：從 GCS 讀取 PDF 並上傳至 Gemini File API。
- 結構化解析：使用 System Instruction 讓 gemini-2.5-flash 輸出
  [{ "page": 1, "elements": [{ "type": "image"|"text", "content", "description" }] }]。
- 多模態：解析結果含圖片精簡描述，供前端編輯器顯示。
- 錯誤處理：針對 150MB 可能產生的解析超時，使用狀態輪詢（_wait_for_file_ready）
  與可選的 FileHandler 重試。
"""

import logging
from typing import Optional

from src.clients.gcs_client import GCSClient
from src.clients.gemini_client import GeminiFileClient
from src.models.schema import PageBlock
from src.services.file_handler import FileHandler

logger = logging.getLogger(__name__)

# 大檔案（如 150MB）輪詢等待時間（秒）
DEFAULT_FILE_READY_TIMEOUT = 900.0
DEFAULT_POLL_INTERVAL = 2.0


class PDFProcessor:
    """
    編排 PDF 結構化解析：GCS 讀取 → 上傳至 Gemini File API（輪詢直到 ACTIVE）→
    呼叫 parse_pdf_structured 取得每頁的 elements（image/text + content + description）。
    """

    def __init__(
        self,
        gcs_client: GCSClient,
        gemini_client: GeminiFileClient,
        file_handler: Optional[FileHandler] = None,
        file_ready_timeout: float = DEFAULT_FILE_READY_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> None:
        self._gcs = gcs_client
        self._gemini = gemini_client
        self._file_handler = file_handler
        self._file_ready_timeout = file_ready_timeout
        self._poll_interval = poll_interval

    def parse_from_gcs(
        self,
        blob_path: str,
        bucket_name: Optional[str] = None,
    ) -> list[PageBlock]:
        """
        從 GCS 讀取 PDF，上傳至 Gemini File API（含狀態輪詢），再以結構化指令解析。
        回傳 [{ page, elements: [{ type, content, description }] }]。
        若 bucket_name 有給則暫時使用該 bucket。
        """
        gcs = self._gcs
        if bucket_name is not None:
            gcs = GCSClient(bucket_name)

        display_name = blob_path.split("/")[-1] or "document.pdf"
        logger.info("parse_from_gcs: reading blob %s", blob_path)
        data = gcs.read_blob_bytes(blob_path)

        if self._file_handler is not None:
            file_uri = self._file_handler.upload_from_stream(
                data=data,
                display_name=display_name,
                mime_type="application/pdf",
            )
        else:
            file_uri = self._gemini.upload_bytes(
                data=data,
                display_name=display_name,
                mime_type="application/pdf",
                file_ready_timeout=self._file_ready_timeout,
                poll_interval=self._poll_interval,
            )

        logger.info("parse_from_gcs: file ready, parsing structured content")
        return self._gemini.parse_pdf_structured(file_uri)
