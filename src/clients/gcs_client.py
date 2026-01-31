"""GCS Client：封裝 Google Cloud Storage 讀取邏輯。"""

from google.cloud import storage


class GCSClient:
    """讀取 GCS 桶內檔案的 Client，僅負責 I/O，不含業務邏輯。"""

    def __init__(self, bucket_name: str, project: str | None = None) -> None:
        self._bucket_name = bucket_name
        self._client = storage.Client(project=project)

    def read_blob_bytes(self, blob_path: str) -> bytes:
        """從 GCS 讀取指定路徑的檔案內容為 bytes。"""
        bucket = self._client.bucket(self._bucket_name)
        blob = bucket.blob(blob_path)
        return blob.download_as_bytes()

    def get_blob_uri(self, blob_path: str) -> str:
        """取得 GCS 物件的 gs:// URI，供其他服務參考。"""
        return f"gs://{self._bucket_name}/{blob_path}"
