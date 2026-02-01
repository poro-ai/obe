# OBE 部署成 Slides 附加元件並安裝 — 檢查清單

使用「部署成附加元件 → 在這份簡報安裝」時，請依序檢查以下項目。

---

## 一、程式與 Manifest 檢查（專案內）

### 1. `gas/appsscript.json`

| 項目 | 說明 | 目前狀態 |
|------|------|----------|
| **addOns** | 必須有，Slides 附加元件才會被辨識 | ✅ `addOns.common` + `addOns.slides: {}` |
| **addOns.common.name** | 顯示名稱（會出現在選單） | ✅ `"OBE"` |
| **addOns.common.logoUrl** | 必填，圖示 URL（需 https） | ✅ 已設 |
| **addOns.slides** | 宣告為 Slides 附加元件 | ✅ `{}` |
| **urlFetchWhitelist** | 根層級，且網址**路徑結尾要有 /** | ✅ 三個網址皆以 `/` 結尾 |
| **oauthScopes** | 依 UrlFetchApp、SlidesApp、HtmlService 列出 | ✅ presentations, script.container.ui, script.external_request, spreadsheets, drive.file |

**urlFetchWhitelist 內容須涵蓋：**

- `https://oauth2.googleapis.com/`
- `https://storage.googleapis.com/`
- `https://asia-east1-obe-project-485614.cloudfunctions.net/`（若 GCF 網址不同，要改成實際網址）

### 2. `gas/Main.js`

| 項目 | 說明 | 目前狀態 |
|------|------|----------|
| **onOpen(e)** | 使用 `createAddonMenu()` 才會出現在「擴充功能」附加元件選單 | ✅ 已用 createAddonMenu，失敗時 fallback createMenu('OBE') |
| **onInstall(e)** | 安裝後呼叫 `onOpen(e)`，選單才會馬上出現 | ✅ 已實作 |
| **showSidebar()** | `createHtmlOutputFromFile('sidebar')` 對應 `sidebar.html`（檔名不含副檔名、大小寫一致） | ✅ 檔名為 `sidebar.html` |

### 3. HTML 檔案

| 項目 | 說明 |
|------|------|
| 左側檔案面板中須有 **sidebar.html**（名稱與大小寫一致） | 與 `createHtmlOutputFromFile('sidebar')` 對應 |

---

## 二、Apps Script 專案（script.google.com）

### 1. 專案來源

- OBE 程式需在 **同一個** Apps Script 專案裡（例如用 clasp push 同步過去）。
- 開啟 [script.google.com](https://script.google.com) → 找到 OBE 專案（或從 clasp 的專案 ID 開啟）。

### 2. 儲存與版本（建議）

- 所有修改後按 **儲存**（Ctrl+S）。
- 若要固定測試版本：**部署 > 管理部署 > 新版本** 或使用「測試用部署」時選「最新程式碼」。

---

## 三、部署成「測試用附加元件」

1. 在 Apps Script 編輯器：**部署 > 測試用部署**（Test deployments）。
2. 若尚未建立過：
   - **建立新的測試**（或 Add test）。
   - **部署類型**：選 **Editor add-on**（編輯器附加元件）。
   - **測試文件**：選 **要安裝 OBE 的那份簡報**（例如「未命名簡報」）。
   - **授權狀態**：依需要選擇（通常選「在存取時登入」即可）。
   - 儲存測試。
3. 在測試用部署畫面按 **安裝**（Install），完成授權。
4. 畫面若提示「已安裝」，表示此 Google 帳號已在該測試中安裝 OBE。

---

## 四、在簡報中確認選單

1. **開啟同一份簡報**（你選為「測試文件」的那份）。
2. **重新整理** 簡報頁面（F5 或重新載入）。
3. 點 **擴充功能**：
   - 若有 **OBE** 或 **開啟 AI 解析側邊欄**，代表附加元件已安裝且選單正常。
   - 若沒有：回到「三」確認測試用部署的「測試文件」是否就是這份簡報，且已按過「安裝」。

---

## 五、若選單仍沒出現 — 可再檢查

| 檢查項 | 作法 |
|--------|------|
| 測試文件是否選對 | 在 **部署 > 測試用部署** 中確認「測試文件」是**這份簡報**。 |
| 是否已按「安裝」 | 同一畫面再按一次 **安裝**，完成授權。 |
| 是否用同一帳號 | 安裝附加元件的 Google 帳號 = 開啟簡報的帳號。 |
| 清除快取再試 | 關閉簡報分頁，重新從雲端硬碟開啟，或無痕視窗再開一次。 |
| 授權與錯誤 | 到 [myaccount.google.com](https://myaccount.google.com) > 安全性 > 已連結的應用程式，確認 OBE/Apps Script 已授權；若曾拒絕，需移除後重新安裝。 |

---

## 六、指令碼內容（Properties）

OBE 會呼叫 GCS 與 GCF，需在 **專案設定 > 指令碼內容** 設定：

- `GCP_SA_CLIENT_EMAIL`
- `GCP_SA_PRIVATE_KEY`
- `GCS_BUCKET`（選填，預設 obe-files）
- `GCF_PARSE_PDF_URL`（選填，預設 asia-east1 的 parse_pdf URL）

以上設好後，附加元件內的「上傳 PDF → GCS → GCF 解析」才會正常。

---

## 快速對照：我該檢查哪裡？

1. **程式與 manifest**：`gas/appsscript.json`、`gas/Main.js`、`sidebar.html` 檔名（見「一、二」）。
2. **同一個專案**：script.google.com 裡開的是 OBE 專案，且已 clasp push 或手動貼齊。
3. **測試用部署**：部署 > 測試用部署 > Editor add-on、測試文件 = 這份簡報、按過「安裝」。
4. **簡報與帳號**：開啟的是「測試文件」那份簡報、用安裝時同一帳號、有重新整理。
5. **後端連線**：指令碼內容已設 GCP/GCS/GCF 相關屬性（見「六」）。

全部對上後，在該簡報的 **擴充功能** 底下就會看到 OBE 並可開啟側邊欄。
