# Slides 替代方案：在瀏覽器開啟編輯器（大畫面、圖片可顯示、可拖拉）

側邊欄受 GAS HtmlService 限制（空間小、圖片常無法顯示）。可改為**在瀏覽器開啟編輯器**：大畫面、圖片正常顯示、可拖拉排序，再一鍵插入至目前簡報。

---

## 流程

1. **在 Google Slides** 開啟 OBE 附加元件（側邊欄或首頁卡片）。
2. 點 **「在瀏覽器開啟編輯器（大畫面・可顯示圖片）」**。
3. 瀏覽器會開新分頁，網址已帶入**目前簡報 ID** 與 **GAS Web App URL**（若已設定）。
4. 在編輯器頁面：
   - **從上次解析結果載入** 或 **貼上 JSON 載入**（若你是在側邊欄先解析過，可先回側邊欄上傳 PDF 解析，再來此頁「從上次解析結果載入」）。
   - 或在上傳頁（index.html）上傳並解析後，會導向編輯器並帶入資料。
5. 編輯、拖拉排序後，點 **「插入至 Google 簡報」** → 會 POST 到 GAS Web App（action=insertToSlides），將**全部內容**插入該簡報的**第一張投影片**。

---

## 設定（GAS 指令碼內容）

| 屬性 | 說明 |
|------|------|
| **EDITOR_BASE_URL** | 編輯器前端網址（例：`https://poro-ai.github.io/obe/`），側邊欄「在瀏覽器開啟編輯器」會開 `EDITOR_BASE_URL/editor.html?presentationId=xxx&gasUrl=yyy`。 |
| **GAS_WEB_APP_URL** | （選填）GAS Web App 的部署網址（例：`https://script.google.com/macros/s/xxx/exec`）。若設定，會自動帶入編輯器，使用者不必手動貼網址。 |

---

## Web App 部署注意

「插入至 Google 簡報」會呼叫 GAS Web App 的 `doPost`（action=insertToSlides），寫入**使用者的簡報**。  
部署 Web App 時請設為 **「以造訪使用者的身分執行」**，否則無法寫入該使用者的簡報。

---

## 與側邊欄的差異

| 項目 | 側邊欄 | 瀏覽器編輯器 |
|------|--------|--------------|
| 畫面大小 | 約 300px 寬 | 整頁，可自訂版面 |
| 圖片顯示 | 受 GAS CSP 限制，常無法顯示 | 正常顯示（一般網頁） |
| 拖拉排序 | 無 | 有（編輯器內拖拉內容塊） |
| 插入目標 | 目前選取的投影片 | 指定簡報的第一張（或可擴充 slideIndex） |

插入邏輯（排版、字型）與側邊欄「插入選取項目至投影片」一致，由 `web_app.js` 的 `_insertElementsIntoSlide` 統一處理。
