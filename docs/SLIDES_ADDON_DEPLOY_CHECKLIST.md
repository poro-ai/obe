# OBE 部署成 Slides 附加元件並安裝 — 檢查清單

**重要：OBE 是「附加元件」、不是「綁定腳本」。** 不需把 Apps Script 綁到某一份簡報；安裝後會以**帳號為單位**生效，同一帳號開任何簡報都能用。之後要給多個不特定使用者：測試階段可分享專案讓對方在專案內按「安裝」、正式階段從市集安裝。

使用「部署成附加元件 → 測試用部署安裝」時，請依序檢查以下項目。

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

## 三、目前介面：測試用部署「沒有安裝網址」，用「安裝」按鈕即可（2025 官方流程）

依 [Google 官方文件](https://developers.google.com/workspace/add-ons/how-tos/testing-workspace-addons)（Test and debug Apps Script Google Workspace add-ons），**未發布附加元件的測試安裝不會提供「安裝網址」**。你看到的畫面會有：

- **選取類型**：Google Workspace 外掛程式  
- **設定**：首要部署作業 ID、部署作業（例如 Test latest code）、Application(s): Slides  
- **安裝**（Install）、**解除安裝**（Uninstall）、**完成**（Done）  

**正確安裝步驟（不需測試文件、不需任何 URL）：**

1. 在 Apps Script 編輯器：**部署** → **測試用部署**（Test deployments）。
2. 在「測試部署作業」畫面直接點 **安裝**（Install）。
3. 點 **完成**（Done）關閉對話框。
4. 開啟 **Google 簡報**（任意一份，或新開一份），必要時 **重新整理**（F5）該分頁。  
   → 附加元件會立即對**目前登入的帳號**生效，選單應出現在 **擴充功能** 或選單列 **OBE**。

**給其他測試者用（沒有可分享的安裝連結時）：**

- 官方做法：**把 Apps Script 專案分享給對方**（對方需有**編輯者**權限）。  
- 對方在自己的電腦：開啟該專案 → **部署** → **測試用部署** → **安裝** → **完成**。  
- 對方再開啟 Google 簡報並重新整理，即可看到 OBE。  
- 正式上線後改為從 **Google Workspace Marketplace** 安裝，才會有「一個連結給所有人安裝」。

---

## 四、在簡報中確認選單（擴充功能沒看到時請看這裡）

1. **開啟任意一份 Google 簡報**，用**剛才在測試用部署按「安裝」時的同一個 Google 帳號**。
2. **重新整理** 簡報頁面（F5）；若已開著簡報，先重新整理再找選單。
3. 找 OBE 入口（**測試安裝時選單常不顯示**，以側邊欄為主）：
   - **側邊欄**：點選單列 **擴充功能**（或右側附加元件圖示）→ 若出現 **OBE** 面板，上面有 **「開啟 AI 解析側邊欄」按鈕**，點下去即開啟上傳 PDF／解析結果的側邊欄。**無需從選單找 OBE。**
   - 選單（若有出現）：**擴充功能** 底下 **OBE** → **開啟 AI 解析側邊欄**，或選單列頂層 **OBE**。
4. 若連側邊欄都沒有 OBE 面板：
   - 到 **擴充功能** → **附加元件** → **管理附加元件**，看是否列出 OBE。若沒有，代表尚未安裝成功，請回到「三」在測試用部署再點一次 **安裝** → **完成**。
   - 確認目前登入的 Google 帳號與在 Apps Script 按「安裝」時相同（右上角頭像）。

---

## 五、若選單仍沒出現 — 可再檢查

| 檢查項 | 作法 |
|--------|------|
| 是否點過「安裝」並「完成」 | 必須在 **部署 > 測試用部署** 畫面點 **安裝**，再點 **完成**，不是只儲存部署設定。 |
| 是否用同一帳號 | 在 Apps Script 按安裝的 Google 帳號 = 開啟簡報的帳號（右上角頭像）。 |
| 管理附加元件有無 OBE | **擴充功能** → **附加元件** → **管理附加元件**：若有 OBE 表示已安裝，再試重新整理簡報或關掉分頁重開。 |
| 重新整理簡報 | 安裝後若簡報早已開啟，務必 **F5 重新整理** 該分頁。 |
| 授權是否被拒絕過 | [myaccount.google.com](https://myaccount.google.com) > 安全性 > 已連結的應用程式：若曾拒絕 OBE/Apps Script，移除後回 Apps Script 再點一次「安裝」。 |

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
3. **測試用部署**：**部署** > **測試用部署** → 點 **安裝** → 點 **完成**（目前介面沒有「測試文件」或「安裝網址」，這是正常）。
4. **簡報與帳號**：開啟**任意**簡報、用按「安裝」時同一 Google 帳號、**重新整理**（F5）簡報分頁。
5. **後端連線**：指令碼內容已設 GCP/GCS/GCF 相關屬性（見「六」）。

全部對上後，在**任意簡報**開啟附加元件時會看到 **OBE** 面板（側邊欄）；點卡片上的 **「開啟 AI 解析側邊欄」** 即可使用。測試安裝時選單列常不顯示 OBE，**以側邊欄內的按鈕為主**即可。  
**給多個測試者**：分享 **Apps Script 專案**（編輯權限），請對方在專案內同樣執行「部署 > 測試用部署 > 安裝 > 完成」。**正式上線**則發布到 Google Workspace Marketplace，使用者從市集安裝即可，無需綁定任何腳本。
