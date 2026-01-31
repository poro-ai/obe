"""Google Cloud Function 入口：處理大型 PDF 解析請求。"""

import functions_framework
from flask import Request, jsonify

from src.clients.gcs_client import GCSClient
from src.clients.gemini_client import GeminiFileClient
from src.services.pdf_parse_service import PDFParseService


@functions_framework.http
def parse_pdf(request: Request):
    """
    HTTP 觸發：接收 bucket 與 blob_path，經 GCS + Gemini File API 解析 PDF。
    Body 範例: { "bucket": "my-bucket", "blob_path": "path/to/file.pdf" }
    """
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        data = request.get_json(silent=True) or {}
        bucket = data.get("bucket")
        blob_path = data.get("blob_path")
        if not bucket or not blob_path:
            return jsonify({"error": "Missing bucket or blob_path"}), 400

        gcs = GCSClient(bucket_name=bucket)
        gemini = GeminiFileClient()  # 使用環境變數 GOOGLE_API_KEY 或 ADC
        service = PDFParseService(gcs_client=gcs, gemini_client=gemini)

        extracts = service.parse_from_gcs(blob_path)
        return jsonify({
            "count": len(extracts),
            "pages": [e.model_dump() for e in extracts],
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
