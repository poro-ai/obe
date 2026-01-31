"""PDF 解析服務：編排 GCS 讀取與 Gemini File API 解析，僅含業務邏輯。"""

from src.clients.gcs_client import GCSClient
from src.clients.gemini_client import GeminiFileClient
from src.models.schema import PageExtract


class PDFParseService:
    """
    編排大 PDF 解析流程：從 GCS 取得檔案 → 上傳至 Gemini File API → 解析為 PageExtract。
    150MB 等級檔案一律經由 Gemini File API，不在記憶體中一次性載入整份 PDF。
    """

    def __init__(self, gcs_client: GCSClient, gemini_client: GeminiFileClient) -> None:
        self._gcs = gcs_client
        self._gemini = gemini_client

    def parse_from_gcs(self, blob_path: str, bucket_name: str | None = None) -> list[PageExtract]:
        """
        從 GCS 讀取 PDF，上傳至 Gemini File API 後解析。
        若 bucket_name 有給則暫時使用該 bucket，否則使用 gcs_client 建構時的 bucket。
        """
        gcs = self._gcs
        if bucket_name is not None:
            gcs = GCSClient(bucket_name)
        data = gcs.read_blob_bytes(blob_path)
        file_uri = self._gemini.upload_bytes(
            data=data,
            display_name=blob_path.split("/")[-1] or "document.pdf",
            mime_type="application/pdf",
        )
        return self._gemini.parse_pdf_with_file_uri(file_uri)
