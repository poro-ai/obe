"""Google Cloud Function 入口：處理大型 PDF 解析請求。"""

import functions_framework
from flask import Request, jsonify

from src.clients.gcs_client import GCSClient
from src.clients.gemini_client import GeminiFileClient
from src.services.processor import PDFProcessor


@functions_framework.http
def parse_pdf(request: Request):
    """
    HTTP 觸發：接收 bucket 與 blob_path，經 GCS + Gemini File API 結構化解析 PDF。
    Body 範例: { "bucket": "my-bucket", "blob_path": "path/to/file.pdf" }
    回傳格式: { "count", "pages": [{ "page", "elements": [{ "type", "content", "description" }] }] }
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
        gemini = GeminiFileClient()
        processor = PDFProcessor(gcs_client=gcs, gemini_client=gemini)

        blocks = processor.parse_from_gcs(blob_path, bucket_name=bucket)
        return jsonify({
            "success": True,
            "count": len(blocks),
            "pages": [b.model_dump() for b in blocks],
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
