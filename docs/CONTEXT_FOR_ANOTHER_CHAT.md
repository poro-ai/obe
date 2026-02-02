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
| 業務邏輯 | PDF 解析編排、圖片擷取 | `src/services/processor.py`, `src/services/pdf_parse_service.py`, `src/services/file_handler.py`, `src/services/pdf_image_extractor.py` |
| 資料模型 | Pydantic | `src/models/schema.py` |

**重要目錄說明：**

- `src/clients/`：GCS、Gemini、ConfigLoader（金鑰/設定）。
- `src/services/processor.py`：**PDFProcessor** — 從 GCS 讀 PDF → **extract_images_by_page**（PyMuPDF 擷取內嵌圖）→ 上傳 Gemini（輪詢 540s）→ **parse_pdf_structured** → **\_fill_image_content** 將擷取到的圖片填入 type=image 且 content 為空的區塊。
- `src/services/pdf_image_extractor.py`：從 PDF bytes 擷取每頁內嵌圖（base64 + mime），每頁最多 10 張、單張最大 500KB；依賴 **pymupdf**（requirements.txt）。
- `src/models/schema.py`：**PageBlock**（page, elements）、**BlockElement**（type, content, description）；另保留 **PageExtract** 舊格式相容。
- `gas/`：GAS 專案檔，以 **clasp** 推送（`npx @google/clasp push`）；根目錄的 `appsscript.json` 與 `gas/appsscript.json` 需一致或以 gas 為準。
- `frontend/`：上傳頁 + 編輯器；編輯器可載入解析結果、拖曳編輯、匯出至 Sheets。

---

## 四、資料流與 API 摘要

### 4.1 上傳並解析 PDF（前端 → GAS → GCF）

1. **前端**：選 PDF → FileReader 讀成 Base64 → POST 到 **GAS Web App**（`Content-Type: text/plain;charset=utf-8`，body 為 JSON，避 CORS 預檢）。
2. **GAS doPost**：解 JSON，取 `pdfBase64`、`fileName` → Base64 解碼 → **上傳 GCS**（`uploads/{timestamp}_{fileName}`）→ **POST 呼叫 GCF** `parse_pdf`，body `{ bucket, blob_path }`。
3. **GCF parse_pdf**：用 **PDFProcessor** 從 GCS 讀 PDF → **extract_images_by_page**（PyMuPDF）擷取內嵌圖 → **Gemini File API** 上傳（輪詢至 ACTIVE，540s）→ **parse_pdf_structured** → **\_fill_image_content** 將擷取到的圖片填入 type=image 且 content 為空的區塊 → 回傳 `{ success, count, pages }`。要看到編輯器內圖片，需**重新部署 GCF**（含 pymupdf）。
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
- **替代方案（瀏覽器編輯器）**：側邊欄受 GAS 限制（空間小、圖片常不顯示）。點「在瀏覽器開啟編輯器」→ 新分頁 `editor.html?presentationId=xxx&gasUrl=yyy&token=zzz`。編輯器載入時若有 `token` 會 **GET gasUrl?action=getParseResult&token=zzz**（跨域用 JSONP）從 Cache 取回資料；**版本**以 **GET gasUrl?callback=xxx**（JSONP）取得。編輯後點「插入至 Google 簡報」會 **POST action=insertToSlides**，由 **web_app.js \_insertToSlides(body)** 寫入該簡報（預設第一張投影片）。**gasUrl 須為 /exec** 且部署「誰可以存取＝所有人」「執行身分＝以我的身分執行」；若需寫入使用者簡報，可另設「以造訪使用者的身分執行」或依需求調整。需設定 **EDITOR_BASE_URL**、**GAS_WEB_APP_URL**。

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
- **GAS_WEB_APP_URL**：GAS Web App **/exec** 部署網址；編輯器需此 URL 取解析結果與版本、POST 插入簡報。編輯器從 GitHub Pages 開啟時須用 **/exec** 且 **「誰可以存取」＝所有人**、**「執行身分」＝以我的身分執行**，否則未登入請求會 302 導向登入。**insertToSlides** 寫入使用者簡報時，該部署可另設「以造訪使用者的身分執行」或使用同一個 /exec（依需求）。

### 5.2 GCF / 本機

- **GEMINI_API_KEY**：Gemini API（ConfigLoader 可從 .env 或 Secret Manager 讀取）。
- GitHub Actions 部署 GCF 時：**GCP_PROJECT_ID**、**GCP_SA_KEY**（服務帳號 JSON）、**GEMINI_API_KEY**。
- GitHub Actions 部署 GAS 時（可選）：**CLASP_JSON**（.clasp.json 內容，單行）、**CLASPRC_JSON**（~/.clasprc.json 完整內容）；見 `DEPLOYMENT.md`。

### 5.3 權限要點

- GAS 用的服務帳號需在 **GCS bucket** 上具 **Storage Object Creator**（否則上傳 403）。
- **appsscript.json**：`oauthScopes`（presentations, script.container.ui, script.external_request, spreadsheets, drive.file 等）、**urlFetchWhitelist**（根層級，網址路徑以 `/` 結尾）、**addOns**（common.name, common.logoUrl, common.homepageTrigger.runFunction: onHomepage, slides.homepageTrigger.runFunction: onSlidesHomepage）。

---

## 六、部署與同步

- **GCF**：push 到 **main** 觸發 GitHub Actions（`.github/workflows/deploy.yml`）**deploy-gcf** job，部署 Cloud Function（parse_pdf）。**deploy-gas** job 會接著執行 **`npx @google/clasp push --force`**，需在 GitHub Secrets 設定 **CLASP_JSON**、**CLASPRC_JSON**（見 `DEPLOYMENT.md`）；未設定時 deploy-gas 會失敗，不影響 GCF。
- **GAS**：本機亦可執行 **`npx @google/clasp push`**（或 `--force`）同步 `gas/` 到 script.google.com；`.clasp.json` 在 .gitignore，需自行設定 scriptId。
- **慣例**：使用者說「**go**」＝**先更新版本號**（gas/web_app.js 的 BACKEND_VERSION 與 tests 內預期版號）→ Quick test → commit → push → **`npx @google/clasp push`**。**「commit and push all」** 亦須含 **clasp push**。GAS 程式變更後需遞增 **BACKEND_VERSION**（patch 兩位數，如 1.0.08）。**GAS 有更新時**：Agent 須提醒使用者重新佈署（/exec 須在 Apps Script 建立新版本並切換），並給出**本次 gas 更新說明**（見 `.cursorrules`）。
- **測試慣例**：**每次修改完系統，都要做 unittest 與 integration test**；**新增功能時須一併新增對應單元測試**（見 `.cursorrules`）。**只跑必要測試**：**Quick**（日常／go 預設）＝`python -m pytest tests/unit/ -v --tb=short`（僅單元，約 20–40s）；**Full**（發布前／CI）＝`python -m pytest tests/ -v --tb=short`（含整合，需網路）。測試目錄：`tests/unit/`（單元）、`tests/test_cloud_connection.py`、`tests/test_doget.py`（整合）。未設定 `GAS_WEBAPP_URL` 時 `test_doget` 會跳過。測試涵蓋缺口與補足說明見 **`docs/TEST_COVERAGE_GAP.md`**。
- **GAS Web App 網址**（供 `test_doget` 等使用）：支援兩個變數，依需要取用。**GAS_WEBAPP_DEV_URL**：測試用，pytest 時優先使用。**GAS_WEBAPP_URL**：正式用；未設 DEV 時 fallback。在 `.env` 寫入上述變數（或執行前設環境變數）；網址從 GAS「部署」→「網路應用程式」取得。`.env` 已在 .gitignore，不需提交。
- **/exec 與 /dev 差異**：**/exec**＝版本化部署，執行的是「部署時選定的那一版」；新 code 要生效**必須重新部署**（建立新版本後，在「管理部署」裡把該 Web App 的版本改為新版本）。**/dev**＝測試部署（Head），執行**目前儲存的程式**；`clasp push` 或編輯器儲存後即生效，不需重新部署；僅供有編輯權限者，不能設「所有人」。詳見 `docs/VERSION_DISPLAY_DEBUG.md` 第零節。

---

## 七、已知慣例與注意點

1. **CORS**：前端對 GAS 使用 `Content-Type: text/plain;charset=utf-8` + JSON body，避免 preflight。
2. **Base64**：GAS 用 `Utilities.base64Encode(str, Utilities.Charset.UTF_8)` 字串簽章，避免 byte array 簽章不相容。
3. **Gemini**：模型為 **gemini-2.5-flash**；結構化解析用 **parse_pdf_structured** + System Instruction，輸出支援 `page`/`page_number`、`description`/`summary`。
4. **舊格式相容**：解析結果可能是舊的 group_id/visual_summary/associated_text；前端與編輯器需能正規化為 `pages[].elements`（type, content, description）。
5. **Slides 選單**：若附加元件測試安裝後仍看不到選單，可改為**將腳本綁定到該簡報**（擴充功能 → Apps Script，貼上 OBE 程式），並用 **createMenu('OBE')** 確保選單出現。**未發布附加元件**測試：在 Apps Script 編輯器點「安裝」按鈕安裝，不需綁定簡報，以帳號為單位生效；詳見 `docs/SLIDES_ADDON_DEPLOY_CHECKLIST.md`。
6. **首頁觸發**：manifest 若有 **addOns.common.homepageTrigger**、**addOns.slides.homepageTrigger**，必須實作 **onHomepage**、**onSlidesHomepage** 並回傳 Card 陣列，否則會報「找不到指令碼函式：onSlidesHomepage」。
7. **側邊欄 UI（sidebar.html）**：頂部隱藏 `<input type="file">`，由質感「上傳 PDF」按鈕觸發；動態進度條三階段「正在讀取檔案...」「正在上傳雲端...」「AI 深度解析中...」；`id="content-list"` 渲染解析結果；類型過濾（全部/僅圖片/僅文字）、手風琴摺疊（accordion）顯示各頁。圖片：**type 不區分大小寫**（Image/image 皆識別）；支援純 base64 字串（自動補 `data:image/png;base64,` 前綴），`<img>` 設 **onerror** 顯示「圖」佔位。
8. **版本號**：單一來源為 **gas/web_app.js** 的 **BACKEND_VERSION**（如 `1.0.06`，**patch 為 2 位數** 01–99）；**getVersion()** 回傳該值。**clasp 推送的是 gas/**（.clasp.json rootDir: ./gas）；根目錄 **web_app.js** 為舊檔/備份，勿當作 GAS 來源。側邊欄與編輯器頁面底部、**首頁卡片**皆顯示版本。側邊欄用 `google.script.run.getVersion()`；編輯器與上傳頁**跨域**時用 **JSONP**（`?callback=xxx`）取版本，同源時用 fetch。GAS 對 /exec 請求常回 **302** 再導向 script.googleusercontent.com/echo → **200 + JSONP**，屬正常；編輯器以 `<script src=".../exec?callback=xxx">` 載入時，跟隨 302 後取得 JSONP 即可顯示版號。版本沒出現時可依 **`docs/VERSION_DISPLAY_DEBUG.md`** 除錯；本機快速測試 GAS 是否回 JSONP：`python scripts/test_gas_jsonp_local.py [GAS_URL]`；檢查 gas/ 是否含版本程式：`python scripts/verify_version_in_gas.py`。
9. **測試與 .env**：`tests/test_doget.py` 優先讀取 **GAS_WEBAPP_DEV_URL**，未設則用 **GAS_WEBAPP_URL**；可從專案根目錄 **.env** 載入（需 `python-dotenv`）。單元測試中 **get_secret** / **project_id** 相關案例已隔離 `os.environ`，避免本機真實環境變數導致失敗。
10. **編輯器跨域**：編輯器從 GitHub Pages 等不同 origin 開啟時，**版本**與**解析結果**（getParseResult）皆以 **JSONP** 向 GAS 請求（GAS doGet 支援 `callback` 回傳 JSONP）。若 URL 無 gasUrl 但有 token 或 presentationId，編輯器會從 **localStorage** 讀上次使用的 GAS 網址補齊。**gasUrl 過長**時 `URLSearchParams.get('gasUrl')` 可能為 null，編輯器已加**備援**：從 `location.search` 手動擷取 `gasUrl=` 後的值。**insertToSlides** 已在 editor.html 實作（按鈕「插入至 Google 簡報」）。**編輯器圖片**：type 不區分大小寫；無 content 時顯示「圖片（目前無預覽）」+ description 佔位；有 base64 時補 `data:image/...;base64,` 前綴。

---

## 八、最近實作摘要（供新 Chat 快速銜接）

- **Slides 側邊欄**：NATIVE sandbox、上傳→進度條三階段→content-list（過濾/手風琴）、base64 圖片前綴與 onerror 佔位、「插入選取項目」「在瀏覽器開啟編輯器」按鈕；側邊欄與首頁卡片顯示版本（getVersion）。**圖片 type** 不區分大小寫。
- **附加元件入口**：雙選單（擴充功能 + 頂層 OBE）、首頁卡片「開啟 AI 解析側邊欄」+ 版本：vX.X.X；未發布測試安裝見 `docs/SLIDES_ADDON_DEPLOY_CHECKLIST.md`。
- **瀏覽器編輯器**：側邊欄點按鈕 → getEditorUrlWithToken → 新分頁 editor.html?presentationId&gasUrl&token；callGcfParse 成功後 \_storeParseResultChunked 存 Cache、回傳 token。編輯器**跨域**時以 **JSONP** 取版本與 getParseResult；**gasUrl 備援**、**insertToSlides** 已實作。**圖片**：type 不區分大小寫；無 content 時顯示「圖片（目前無預覽）」+ description；有 base64 時補 data URI 前綴。
- **PDF 圖片擷取（GCF）**：**src/services/pdf_image_extractor.py** 用 **PyMuPDF** 從 PDF 擷取每頁內嵌圖（base64 + mime），**processor.parse_from_gcs** 在 Gemini 解析後以 **\_fill_image_content** 填入 type=image 且 content 為空的區塊。每頁最多 10 張、單張最大 500KB。需**重新部署 GCF**（requirements.txt 含 pymupdf）後重新解析 PDF 才會在編輯器看到圖片。
- **版本與 GAS 部署**：**gas/web_app.js** 為 clasp 來源；BACKEND_VERSION patch 兩位數（1.0.08）。**go 前須先更新版本號**（web_app.js + tests 預期）。編輯器用 **/exec** 時部署須「誰可以存取＝所有人」「執行身分＝以我的身分執行」。GAS 有更新時 Agent 須**提醒重新佈署**並給**本次 gas 更新說明**（.cursorrules）。
- **CI 部署**：`.github/workflows/deploy.yml` 含 **deploy-gcf**（Cloud Function）與 **deploy-gas**（clasp push）；deploy-gas 需 **CLASP_JSON**、**CLASPRC_JSON**（見 `DEPLOYMENT.md`）。
- **測試與部署**：**go**＝更新版號 → Quick test → commit → push → **clasp push**；**「commit and push all」** 含 **clasp push**。Full：`pytest tests/`。單元含 processor.\_fill_image_content、pdf_image_extractor 邏輯（processor 整合）。涵蓋見 `docs/TEST_COVERAGE_GAP.md`。

---

## 九、檔案對照速查

| 用途 | 路徑 |
|------|------|
| GCF 入口 | `main.py` |
| PDF 解析編排（含圖片填入） | `src/services/processor.py` |
| PDF 內嵌圖擷取 | `src/services/pdf_image_extractor.py` |
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
| 本機快速測 GAS JSONP（版本／getParseResult） | `scripts/test_gas_jsonp_local.py [GAS_URL]` |
| CI 部署（GCF + GAS） | `.github/workflows/deploy.yml` |
| 部署與 GitHub Secrets（含 CLASP_*） | `DEPLOYMENT.md` |

---

以上為 OBE-Project 的架構、背景與最近實作重點，供新 Chat 作為 context 延續開發或除錯時使用。
