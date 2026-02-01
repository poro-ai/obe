# 測試涵蓋缺口說明

已補足 Python 後端單元測試（63 個測試）。以下為涵蓋範圍與仍無自動化測試的部分。

---

## 一、已涵蓋的範圍

| 模組／功能 | 測試檔 | 說明 |
|------------|--------|------|
| **ConfigLoader** | tests/unit/test_config_loader.py (7) | 本機/生產模式、get_secret、env_mode、專案 ID 與例外 |
| **GeminiFileClient** | tests/unit/test_gemini_client.py (8) | upload_file、upload_bytes、parse_pdf_with_file_uri、parse_response（PageExtract/PageBlock） |
| **GAS Base64／簽章慣例** | tests/unit/test_gas_base64url.py | Base64 URL 編碼、GAS 簽章須用字串等 |
| **GAS doGet** | tests/test_doget.py (1) | 整合測試：GET Web App，驗證 version、params 等 |
| **GCF parse_pdf 連線** | tests/test_cloud_connection.py (1) | 整合測試：POST 已部署的 parse_pdf，驗證端點可連、有回應 |

---

## 二、已補足（Python 單元測試）

| 模組／功能 | 測試檔 | 說明 |
|------------|--------|------|
| **main.parse_pdf** | tests/unit/test_main_parse_pdf.py | GET→405、缺 bucket/blob_path→400、空 body→400、有效 POST→200、非 RETRYABLE→500、RETRYABLE 重試用盡→500。 |
| **PDFProcessor** (processor.py) | tests/unit/test_processor.py | parse_from_gcs 編排（mock GCS + Gemini）、bucket_name 切換、display_name、例外傳遞。 |
| **GCSClient** (gcs_client.py) | tests/unit/test_gcs_client.py | read_blob_bytes、get_blob_uri、init bucket_name，mock google.cloud.storage。 |
| **FileHandler** (file_handler.py) | tests/unit/test_file_handler.py | upload_to_gemini（成功、檔案不存在、重試）、upload_from_stream（bytes/BinaryIO、重試、無效型別），mock GeminiFileClient。 |
| **schema** (models/schema.py) | tests/unit/test_schema.py | BlockElement、PageBlock、PageExtract、ImageTextExtract 必填／型別／ge=1 驗證。 |

**PDFParseService** (pdf_parse_service.py)：仍無單元測試；若仍在使用可補測，若已由 PDFProcessor 取代可視為 legacy。

---

## 三、尚未涵蓋或僅間接涵蓋的範圍

### 1. GAS（Apps Script）

| 功能 | 說明 |
|------|------|
| **doPost** | 無自動化測試：上傳 PDF、呼叫 GCF、回傳 pages；需另建測試（如 clasp run 或手動／外部腳本）。 |
| **action=saveToSheets** | 無自動化測試。 |
| **action=insertToSlides** | 無自動化測試。 |
| **getParseResult / token** | 無自動化測試。 |
| **getVersion** | 僅透過 test_doget 的 doGet 間接驗證 version 欄位存在。 |

### 2. 前端（frontend/）

| 功能 | 說明 |
|------|------|
| **index.html / script.js** | 無自動化測試（上傳、進度、版本顯示、JSONP 等）。可考慮 E2E 或手動檢查。 |
| **editor.html** | 無自動化測試（載入 token、插入簡報、版本等）。 |

---

## 四、結論與建議

- **結論**：**Python 後端**已補足單元測試（main、PDFProcessor、GCSClient、FileHandler、schema）；**GAS doPost** 與 **前端**仍無自動化測試。
- **建議**：GAS doPost 若需自動化可考慮獨立腳本呼叫 Web App 或 clasp run；前端可維持手動或後續加 E2E。
