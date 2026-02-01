# OBE-Project 系統架構與背景 — 給另一個 Chat 的 Context

本文件為 OBE-Project 的**重點整理**，供作為後續對話的 context 使用。

**更新約定：** 當對話明顯變長或已被 summarize 時，Agent 應主動整理並更新本文件；使用者說「更新 context 文件」或「整理 CONTEXT」時，一律執行更新。詳見 `.cursorrules`「Context 文件更新約定」。

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

- **Main.js**：`onOpen(e)` 同時建立 **createAddonMenu()**（擴充功能下）與 **createMenu('OBE')**（頂層），確保測試安裝時至少一處能看到選單；`onInstall(e)` 呼叫 onOpen；**onSlidesHomepage(e)** / **onHomepage(e)** 回傳 Card（manifest 的 homepageTrigger 必要）。**首頁卡片**已加「開啟 AI 解析側邊欄」按鈕，使用者看不到選單時也可從卡片進入。
- **showSidebar()**：`HtmlService.createHtmlOutputFromFile('sidebar').setSandboxMode(HtmlService.SandboxMode.NATIVE)` 載入 `sidebar.html`，**NATIVE** 才能顯示 `data:` 圖片；若出現「iframe allow-scripts + allow-same-origin 可逃脫 sandbox」警告可忽略。
- **getEditorUrlWithToken(editorToken)**：回傳 `{ url }`，為瀏覽器編輯器網址，帶 **presentationId**、**gasUrl**、**token**（用於向 GAS 取回解析結果）。側邊欄按鈕「在瀏覽器開啟編輯器（大畫面・可顯示圖片）」開啟此 URL。
- **uploadToGcs(base64, fileName)**、**callGcfParse(bucket, objectName)**：與 web_app 邏輯一致。**callGcfParse 成功後**：GAS 以 **\_storeParseResultChunked** 將解析結果分塊暫存至 **CacheService**，並回傳 **token** 給 Main.js 存成 `savedEditorToken`，供組裝編輯器 URL。
- **insertElementsToSlide(elements)**：將選取的 elements（type, content, description）插入目前投影片 — 圖片 30% 寬置左、文字方塊微軟正黑體 14pt 置右，每項下移 50pt。
- **替代方案（瀏覽器編輯器）**：側邊欄受 GAS 限制（空間小、圖片常不顯示）。點「在瀏覽器開啟編輯器」→ 新分頁 `editor.html?presentationId=xxx&gasUrl=yyy&token=zzz`。編輯器載入時若有 `token` 會 **GET gasUrl?action=getParseResult&token=zzz** 從 Cache 取回資料；編輯後點「插入至 Google 簡報」會 **POST action=insertToSlides**，由 **web_app.js \_insertToSlides(body)** 用 `SlidesApp.openById(presentationId)` 寫入該簡報（預設第一張投影片）。需設定 **EDITOR_BASE_URL**、**GAS_WEB_APP_URL**；Web App 部署應「以造訪使用者的身分執行」以具備簡報寫入權限。

### 4.5 解析結果暫存與編輯器 token（web_app.js）

- **doGet**：支援 `action=getParseResult&token=xxx`，從 **CacheService** 取回先前 **\_storeParseResultChunked** 暫存的解析結果，供編輯器載入。**跨域**：當 URL 帶 `callback=函式名` 時，回傳 **JSONP**（`callback(JSON)`），供編輯器從 GitHub Pages 等不同 origin 取版本與解析結果，避開 CORS。
- **doPost**：**action=insertToSlides** 時，body 含 `presentationId`、`elements`；**\_insertToSlides(body)** 將 elements 插入指定簡報。

---

## 五、環境變數、Secrets 與權限

### 5.1 GAS（指令碼內容）

- **GCP_SA_CLIENT_EMAIL**、**GCP_SA_PRIVATE_KEY**：服務帳號，用於 JWT 取得 GCP access token，上傳 GCS。
- **GCS_BUCKET**：預設 `obe-files`。
- **GCF_PARSE_PDF_URL**：parse_pdf 的 URL（如 asia-east1）。
- **SPREADSHEET_ID**（選填）：saveToSheets 時若已設則寫入該試算表，否則新建。
- **EDITOR_BASE_URL**：前端編輯器網址（如 GitHub Pages URL），供組裝「在瀏覽器開啟編輯器」連結。
- **GAS_WEB_APP_URL**：GAS Web App 部署網址；編輯器需此 URL 取解析結果與版本、POST 插入簡報。Web App 部署應設「以造訪使用者的身分執行」以具備簡報寫入權限。

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
- **慣例**：使用者說「**go**」＝test → commit → push → **`npx @google/clasp push`**（先跑 test，通過才提交；最後同步 gas/ 到 Apps Script）。GAS 程式變更後需遞增 **BACKEND_VERSION**（如 `web_app.js`）。
- **測試慣例**：**每次修改完系統，都要做 unittest 與 integration test**；**新增功能時須一併新增對應單元測試**（見 `.cursorrules`）。**只跑必要測試**：**Quick**（日常／go 預設）＝`python -m pytest tests/unit/ -v --tb=short`（僅單元，約 20–40s）；**Full**（發布前／CI）＝`python -m pytest tests/ -v --tb=short`（含整合，需網路）。測試目錄：`tests/unit/`（單元）、`tests/test_cloud_connection.py`、`tests/test_doget.py`（整合）。未設定 `GAS_WEBAPP_URL` 時 `test_doget` 會跳過。測試涵蓋缺口與補足說明見 **`docs/TEST_COVERAGE_GAP.md`**。
- **GAS Web App 網址**（供 `test_doget` 等使用）：支援兩個變數，依需要取用。**GAS_WEBAPP_DEV_URL**：測試用，pytest 時優先使用。**GAS_WEBAPP_URL**：正式用；未設 DEV 時 fallback。在 `.env` 寫入上述變數（或執行前設環境變數）；網址從 GAS「部署」→「網路應用程式」取得。`.env` 已在 .gitignore，不需提交。

---

## 七、已知慣例與注意點

1. **CORS**：前端對 GAS 使用 `Content-Type: text/plain;charset=utf-8` + JSON body，避免 preflight。
2. **Base64**：GAS 用 `Utilities.base64Encode(str, Utilities.Charset.UTF_8)` 字串簽章，避免 byte array 簽章不相容。
3. **Gemini**：模型為 **gemini-2.5-flash**；結構化解析用 **parse_pdf_structured** + System Instruction，輸出支援 `page`/`page_number`、`description`/`summary`。
4. **舊格式相容**：解析結果可能是舊的 group_id/visual_summary/associated_text；前端與編輯器需能正規化為 `pages[].elements`（type, content, description）。
5. **Slides 選單**：若附加元件測試安裝後仍看不到選單，可改為**將腳本綁定到該簡報**（擴充功能 → Apps Script，貼上 OBE 程式），並用 **createMenu('OBE')** 確保選單出現。**未發布附加元件**測試：在 Apps Script 編輯器點「安裝」按鈕安裝，不需綁定簡報，以帳號為單位生效；詳見 `docs/SLIDES_ADDON_DEPLOY_CHECKLIST.md`。
6. **首頁觸發**：manifest 若有 **addOns.common.homepageTrigger**、**addOns.slides.homepageTrigger**，必須實作 **onHomepage**、**onSlidesHomepage** 並回傳 Card 陣列，否則會報「找不到指令碼函式：onSlidesHomepage」。
7. **側邊欄 UI（sidebar.html）**：頂部隱藏 `<input type="file">`，由質感「上傳 PDF」按鈕觸發；動態進度條三階段「正在讀取檔案...」「正在上傳雲端...」「AI 深度解析中...」；`id="content-list"` 渲染解析結果；類型過濾（全部/僅圖片/僅文字）、手風琴摺疊（accordion）顯示各頁。圖片：支援純 base64 字串（自動補 `data:image/png;base64,` 前綴），`<img>` 設 **onerror** 顯示「圖」佔位。
8. **版本號**：單一來源為 **gas/web_app.js** 的 **BACKEND_VERSION**（如 `1.0.5`）；**getVersion()** 回傳該值。側邊欄與編輯器頁面底部、**首頁卡片**皆顯示版本。側邊欄用 `google.script.run.getVersion()`；編輯器與上傳頁**跨域**時用 **JSONP**（`?callback=xxx`）取版本，同源時用 fetch。版本沒出現時可依 **`docs/VERSION_DISPLAY_DEBUG.md`** 除錯；本機檢查 gas/ 是否含版本程式：`python scripts/verify_version_in_gas.py`。
9. **測試與 .env**：`tests/test_doget.py` 優先讀取 **GAS_WEBAPP_DEV_URL**，未設則用 **GAS_WEBAPP_URL**；可從專案根目錄 **.env** 載入（需 `python-dotenv`）。單元測試中 **get_secret** / **project_id** 相關案例已隔離 `os.environ`，避免本機真實環境變數導致失敗。
10. **編輯器跨域**：編輯器從 GitHub Pages 等不同 origin 開啟時，**版本**與**解析結果**（getParseResult）皆以 **JSONP** 向 GAS 請求（GAS doGet 支援 `callback` 回傳 JSONP）。若 URL 無 gasUrl 但有 token 或 presentationId，編輯器會從 **localStorage** 讀上次使用的 GAS 網址補齊。

---

## 八、最近實作摘要（供新 Chat 快速銜接）

- **Slides 側邊欄**：NATIVE sandbox、上傳→進度條三階段→content-list（過濾/手風琴）、base64 圖片前綴與 onerror 佔位、「插入選取項目」「在瀏覽器開啟編輯器」按鈕；側邊欄與首頁卡片顯示版本（getVersion）。
- **附加元件入口**：雙選單（擴充功能 + 頂層 OBE）、首頁卡片「開啟 AI 解析側邊欄」+ 版本：vX.X.X；未發布測試安裝見 `docs/SLIDES_ADDON_DEPLOY_CHECKLIST.md`。
- **瀏覽器編輯器**：側邊欄點按鈕 → getEditorUrlWithToken → 新分頁 editor.html?presentationId&gasUrl&token；callGcfParse 成功後 \_storeParseResultChunked 存 Cache、回傳 token。編輯器**跨域**時以 **JSONP** 取版本與 getParseResult（GAS doGet 支援 `callback` 回傳 JSONP）；無 URL gasUrl 時從 **localStorage** 補 GAS 網址。POST insertToSlides → \_insertToSlides 寫入指定簡報。
- **版本**：web_app.js BACKEND_VERSION、getVersion()；sidebar / editor / 首頁卡片 / index 上傳頁皆顯示；跨域用 JSONP。除錯見 `docs/VERSION_DISPLAY_DEBUG.md`、`python scripts/verify_version_in_gas.py`。
- **測試**：**go**＝**Quick**（`pytest tests/unit/`）→ commit → push → **clasp push**；要完整再跑 **Full**（`pytest tests/`）。**新增功能須一併新增單元測試**。已補：schema、gcs_client、processor、file_handler、main_parse_pdf、gas_doget_jsonp_contract、editor_gas_contract。涵蓋說明見 `docs/TEST_COVERAGE_GAP.md`。

---

## 九、檔案對照速查

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
| 版本顯示除錯 | `docs/VERSION_DISPLAY_DEBUG.md` |
| 測試涵蓋缺口與補足 | `docs/TEST_COVERAGE_GAP.md` |
| 本機檢查 gas/ 版本程式 | `scripts/verify_version_in_gas.py` |

---

以上為 OBE-Project 的架構、背景與最近實作重點，供新 Chat 作為 context 延續開發或除錯時使用。
