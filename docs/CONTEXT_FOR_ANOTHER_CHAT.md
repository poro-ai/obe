# OBE-Project 系統架構與背景 — 給另一個 Chat 的 Context

本文件為 OBE-Project 的**重點整理**，供作為後續對話的 context 使用。

---

## 一、專案目的與背景

- **OBE-Project**：處理**大型圖文 PDF** 的解析與編輯流程，整合 **Google Cloud Function (GCF)**、**Google Apps Script (GAS)**、**GCS**、**Gemini File API**、**Google Sheets**、**Google Slides**。
- **核心流程**：使用者上傳 PDF → 存到 GCS → 呼叫 GCF 用 **Gemini 2.5 Flash** 做結構化解析（每頁圖片＋文字）→ 結果可供**網頁編輯器**編輯、匯出至 **Google Sheets**，或在 **Google Slides 附加元件**中上傳、解析、插入投影片。
- **大檔案**：支援約 150MB 等級 PDF，透過 Gemini File API 上傳與輪詢（540s timeout），GCF 內建逾時重試。

---

## 二、系統架構概覽

```
[ 使用者 ]
    │
    ├─ 網頁前端 (frontend/) ──────► GAS Web App (doPost) ──► GCS 上傳 PDF
    │       │                              │
    │       │                              └──► 呼叫 GCF parse_pdf
    │       │                                        │
    │       │                                        ▼
    │       │                              GCF: GCS 讀取 → Gemini File API 上傳
    │       │                                    → 結構化解析 → 回傳 pages
    │       │
    │       ◄── 解析結果 (pages[]) ────────────────┘
    │       │
    │       ├─ 可存 sessionStorage，導向 editor.html 編輯
    │       └─ 編輯器可 POST action=saveToSheets → GAS 寫入 Google Sheets
    │
    └─ Google Slides 附加元件 (gas/Main.js + sidebar.html)
            │
            ├─ 選單：擴充功能 → OBE → 開啟 AI 解析側邊欄
            ├─ 側邊欄：上傳 PDF → uploadToGcs → callGcfParse → 顯示結果
            └─ 插入選取項目：insertElementsToSlide(elements) → 投影片插入圖/文
```

- **前端**：靜態 HTML/JS（可放 GitHub Pages），與 GAS 通訊。
- **GAS**：橋接層 — 收 Base64 PDF、上傳 GCS、呼叫 GCF、回傳 JSON；另處理 saveToSheets、Slides 側邊欄與選單。
- **GCF**：Python 3，接收 `bucket` + `blob_path`，從 GCS 讀 PDF → 上傳 Gemini File API → 結構化解析 → 回傳 `pages`。
- **GCS**：暫存上傳的 PDF；GAS 與 GCF 皆需有權限（GAS 用服務帳號 JWT 上傳）。

---

## 三、技術棧與目錄結構

| 層級 | 技術 | 主要目錄/檔案 |
|------|------|----------------|
| 前端 | 靜態 HTML/JS，Tailwind（編輯器） | `frontend/index.html`, `frontend/script.js`, `frontend/editor.html` |
| GAS | Apps Script (V8)，HtmlService，CardService | `gas/Main.js`, `gas/web_app.js`, `gas/sidebar.html`, `gas/appsscript.json` |
| GCF | Python 3，Flask (functions_framework) | `main.py`, `src/` |
| 儲存/API | GCS，Gemini File API | `src/clients/gcs_client.py`, `src/clients/gemini_client.py` |
| 業務邏輯 | PDF 解析編排 | `src/services/processor.py`, `src/services/pdf_parse_service.py`, `src/services/file_handler.py` |
| 資料模型 | Pydantic | `src/models/schema.py` |

**重要目錄說明：**

- `src/clients/`：GCS、Gemini、ConfigLoader（金鑰/設定）。
- `src/services/processor.py`：**PDFProcessor** — 從 GCS 讀 PDF → 上傳 Gemini（輪詢 540s）→ 呼叫 **parse_pdf_structured** 得結構化結果。
- `src/models/schema.py`：**PageBlock**（page, elements）、**BlockElement**（type, content, description）；另保留 **PageExtract** 舊格式相容。
- `gas/`：GAS 專案檔，以 **clasp** 推送（`npx @google/clasp push`）；根目錄的 `appsscript.json` 與 `gas/appsscript.json` 需一致或以 gas 為準。
- `frontend/`：上傳頁 + 編輯器；編輯器可載入解析結果、拖曳編輯、匯出至 Sheets。

---

## 四、資料流與 API 摘要

### 4.1 上傳並解析 PDF（前端 → GAS → GCF）

1. **前端**：選 PDF → FileReader 讀成 Base64 → POST 到 **GAS Web App**（`Content-Type: text/plain;charset=utf-8`，body 為 JSON，避 CORS 預檢）。
2. **GAS doPost**：解 JSON，取 `pdfBase64`、`fileName` → Base64 解碼 → **上傳 GCS**（`uploads/{timestamp}_{fileName}`）→ **POST 呼叫 GCF** `parse_pdf`，body `{ bucket, blob_path }`。
3. **GCF parse_pdf**：用 **PDFProcessor** 從 GCS 讀 PDF → **Gemini File API** 上傳（輪詢至 ACTIVE，540s）→ **parse_pdf_structured**（System Instruction 要求每頁圖片＋文字、20 字內描述）→ 回傳 `{ success, count, pages }`。
4. **回傳格式**：`pages`: `[{ page: number, elements: [{ type: "image"|"text", content: string, description: string }] }]`。前端可存 `sessionStorage` 並導向 `editor.html`。

### 4.2 GCF parse_pdf 介面

- **方法**：POST  
- **Body**：`{ "bucket": "obe-files", "blob_path": "uploads/xxx/file.pdf" }`  
- **回傳**：`{ "success": true, "count": N, "pages": [ PageBlock ] }`；錯誤時 `{ "success": false, "error": "..." }`  
- **逾時與重試**：File API 輪詢 540s；可重試例外（TimeoutError 等）最多 2 次，指數退避。

### 4.3 GAS doPost 行為

- **一般上傳**：body 含 `pdfBase64`、`fileName` → 上傳 GCS → 呼叫 GCF → 回傳 `{ success, statusCode, count, pages, error, version }`。
- **action=saveToSheets**：body 含 `action: "saveToSheets"`, `pages` → 寫入 Google Sheets（新建或使用 SPREADSHEET_ID），回傳 `{ success, sheetUrl }`。

### 4.4 Google Slides 附加元件

- **Main.js**：`onOpen(e)` 用 createAddonMenu（或 fallback createMenu('OBE')）、`onInstall(e)` 呼叫 onOpen、**onSlidesHomepage(e)** / **onHomepage(e)** 回傳 Card（manifest 的 homepageTrigger 必要）。
- **showSidebar()**：`HtmlService.createHtmlOutputFromFile('sidebar')` 載入 `sidebar.html`（檔名須一致）。
- **getEditorUrlWithPresentationId()**：回傳 `{ url }`，為「瀏覽器編輯器」網址（含目前簡報 ID、GAS Web App URL）。側邊欄按鈕「在瀏覽器開啟編輯器」可開啟此 URL，大畫面、圖片可顯示、可拖拉，再從編輯器「插入至 Google 簡報」。
- **uploadToGcs(base64, fileName)**、**callGcfParse(bucket, objectName)**：與 web_app 邏輯一致，供側邊欄呼叫。
- **insertElementsToSlide(elements)**：將選取的 elements（type, content, description）插入目前投影片 — 圖片 30% 寬置左、文字方塊微軟正黑體 14pt 置右，每項下移 50pt。
- **替代方案**：側邊欄受 GAS 限制（空間小、圖片常不顯示）。可點「在瀏覽器開啟編輯器」→ 開新分頁到 `editor.html?presentationId=xxx&gasUrl=yyy`，在編輯器載入解析結果、拖拉排序後，點「插入至 Google 簡報」；GAS Web App doPost `action=insertToSlides` 會寫入該簡報。見 `docs/SLIDES_EDITOR_ALTERNATIVE.md`。

---

## 五、環境變數、Secrets 與權限

### 5.1 GAS（指令碼內容）

- **GCP_SA_CLIENT_EMAIL**、**GCP_SA_PRIVATE_KEY**：服務帳號，用於 JWT 取得 GCP access token，上傳 GCS。
- **GCS_BUCKET**：預設 `obe-files`。
- **GCF_PARSE_PDF_URL**：parse_pdf 的 URL（如 asia-east1）。
- **SPREADSHEET_ID**（選填）：saveToSheets 時若已設則寫入該試算表，否則新建。

### 5.2 GCF / 本機

- **GEMINI_API_KEY**：Gemini API（ConfigLoader 可從 .env 或 Secret Manager 讀取）。
- GitHub Actions 部署 GCF 時：**GCP_PROJECT_ID**、**GCP_SA_KEY**（服務帳號 JSON）、**GEMINI_API_KEY**。

### 5.3 權限要點

- GAS 用的服務帳號需在 **GCS bucket** 上具 **Storage Object Creator**（否則上傳 403）。
- **appsscript.json**：`oauthScopes`（presentations, script.container.ui, script.external_request, spreadsheets, drive.file 等）、**urlFetchWhitelist**（根層級，網址路徑以 `/` 結尾）、**addOns**（common.name, common.logoUrl, common.homepageTrigger.runFunction: onHomepage, slides.homepageTrigger.runFunction: onSlidesHomepage）。

---

## 六、部署與同步

- **GCF**：push 到 **main** 觸發 GitHub Actions（`.github/workflows/deploy.yml`），只部署 Cloud Function，不部署 GAS。
- **GAS**：本機執行 **`npx @google/clasp push`** 同步 `gas/` 到 script.google.com；`.clasp.json` 在 .gitignore，需自行設定 scriptId。
- **慣例**：助理執行「commit and push」時會一併執行 clasp push；GAS 程式變更後需遞增 **BACKEND_VERSION**（如 `web_app.js`）。

---

## 七、已知慣例與注意點

1. **CORS**：前端對 GAS 使用 `Content-Type: text/plain;charset=utf-8` + JSON body，避免 preflight。
2. **Base64**：GAS 用 `Utilities.base64Encode(str, Utilities.Charset.UTF_8)` 字串簽章，避免 byte array 簽章不相容。
3. **Gemini**：模型為 **gemini-2.5-flash**；結構化解析用 **parse_pdf_structured** + System Instruction，輸出支援 `page`/`page_number`、`description`/`summary`。
4. **舊格式相容**：解析結果可能是舊的 group_id/visual_summary/associated_text；前端與編輯器需能正規化為 `pages[].elements`（type, content, description）。
5. **Slides 選單**：若附加元件測試安裝後仍看不到選單，可改為**將腳本綁定到該簡報**（擴充功能 → Apps Script，貼上 OBE 程式），並用 **createMenu('OBE')** 確保選單出現。
6. **首頁觸發**：manifest 若有 **addOns.common.homepageTrigger**、**addOns.slides.homepageTrigger**，必須實作 **onHomepage**、**onSlidesHomepage** 並回傳 Card 陣列，否則會報「找不到指令碼函式：onSlidesHomepage」。

---

## 八、檔案對照速查

| 用途 | 路徑 |
|------|------|
| GCF 入口 | `main.py` |
| PDF 解析編排 | `src/services/processor.py` |
| Gemini 上傳與結構化解析 | `src/clients/gemini_client.py` |
| 結構化結果模型 | `src/models/schema.py`（PageBlock, BlockElement） |
| GAS Web App（上傳/Sheets） | `gas/web_app.js` |
| GAS Slides 選單/側邊欄/插入 | `gas/Main.js` |
| Slides 側邊欄 UI | `gas/sidebar.html` |
| GAS manifest | `gas/appsscript.json`（與根目錄 appsscript.json 一致） |
| 前端上傳頁 | `frontend/index.html`, `frontend/script.js` |
| 前端編輯器 | `frontend/editor.html` |
| 部署說明 | `DEPLOYMENT.md` |
| Slides 附加元件檢查清單 | `docs/SLIDES_ADDON_DEPLOY_CHECKLIST.md` |

---

以上為 OBE-Project 的架構與背景重點，供後續 Chat 延續開發或除錯時使用。
