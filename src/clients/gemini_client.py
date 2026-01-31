"""Gemini Client：使用 Gemini File API 處理大檔案上傳與解析。"""

import json
import tempfile
import time
from pathlib import Path

import google.generativeai as genai

from src.clients.config_loader import ConfigLoader
from src.models.schema import PageExtract


class GeminiFileClient:
    """
    透過 Gemini File API 上傳並解析大型 PDF（如 150MB）。
    大檔案需先上傳至 File API，再以 file URI 呼叫 generate_content，避免記憶體一次性載入。
    金鑰由 ConfigLoader 統一取得（依 ENV_MODE 從 .env 或 Secret Manager）。
    """

    def __init__(self, api_key: str | None = None, config_loader: ConfigLoader | None = None) -> None:
        loader = config_loader or ConfigLoader()
        key = api_key or loader.get_secret("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    def upload_file(self, file_path: str | Path, mime_type: str = "application/pdf") -> str:
        """
        使用 File API 上傳檔案，回傳 file URI。
        適用於大型 PDF，不會將整檔載入記憶體。
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        uploaded = genai.upload_file(path=str(path), mime_type=mime_type)
        return self._wait_for_file_ready(uploaded.name)

    def upload_bytes(self, data: bytes, display_name: str, mime_type: str = "application/pdf") -> str:
        """
        上傳 bytes 至 File API（適合從 GCS 讀取後的小塊或中繼資料）。
        genai.upload_file 僅接受 path=，故先寫入暫存檔再上傳。
        """
        suffix = Path(display_name).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(data)
            path = f.name
        try:
            uploaded = genai.upload_file(path=path, mime_type=mime_type)
            return self._wait_for_file_ready(uploaded.name)
        finally:
            Path(path).unlink(missing_ok=True)

    def _wait_for_file_ready(self, file_name: str, poll_interval: float = 2.0, timeout: float = 600.0) -> str:
        """輪詢直到檔案狀態為 ACTIVE，回傳可用於 generate_content 的 file URI。"""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            state = genai.get_file(file_name).state
            if state.name == "ACTIVE":
                return f"https://generativelanguage.googleapis.com/v1beta/{file_name}"
            if state.name == "FAILED":
                raise RuntimeError(f"File upload failed: {file_name}")
            time.sleep(poll_interval)
        raise TimeoutError(f"File not ready within {timeout}s: {file_name}")

    def parse_pdf_with_file_uri(self, file_uri: str) -> list[PageExtract]:
        """
        以 File API 回傳的 file URI 呼叫 generate_content，解析 PDF 並回傳結構化結果。
        實際 prompt 與解析邏輯可依需求擴充。
        """
        response = self._model.generate_content(
            [
                "請分析此 PDF，針對每一頁或每個圖文區塊，輸出：group_id、視覺摘要(visual_summary)、對應文字(associated_text)、頁碼(page_number)。",
                genai.types.Part.from_uri(file_uri=file_uri, mime_type="application/pdf"),
            ]
        )
        return self._parse_response_to_page_extracts(response)

    def _parse_response_to_page_extracts(self, response) -> list[PageExtract]:
        """將 Gemini 回應轉成 PageExtract 列表；實作可依實際回應格式調整。"""
        extracts: list[PageExtract] = []
        text = (response.text or "").strip()
        if not text:
            return extracts

        # 簡化：依行或區塊解析，實際可改為 JSON 或更嚴謹的解析
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    extracts.append(PageExtract(**item))
            elif isinstance(data, dict) and "pages" in data:
                for item in data["pages"]:
                    extracts.append(PageExtract(**item))
        except (json.JSONDecodeError, TypeError):
            # 若為非 JSON 文字，回傳單一區塊占位
            extracts.append(
                PageExtract(
                    group_id="default",
                    visual_summary="",
                    associated_text=text[:5000],
                    page_number=1,
                )
            )
        return extracts
