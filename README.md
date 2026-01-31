# OBE-Project

處理大型圖文 PDF 的 Google Cloud Function (GCF) 專案，整合 Gemini File API、GCS、Google Sheets 與 GAS。

## 專案結構

- `src/clients/` — API 與 I/O（Gemini、GCS、ConfigLoader）
- `src/services/` — 業務邏輯（PDF 解析、FileHandler）
- `src/models/` — Pydantic 資料模型
- `gas/` — Google Apps Script 代碼（clasp）
- `frontend/` — 前端頁面（與 GCF 通訊）

## 快速開始

1. 複製 `.env` 範本，填入 `GEMINI_API_KEY`、`PROJECT_ID`、`GCS_BUCKET_NAME` 等。
2. 執行 GCP 基礎設施設定：`./setup_project.sh YOUR_PROJECT_ID`
3. 本地執行 GCF：`functions-framework --target=parse_pdf --debug`
4. 前端：開啟 `frontend/index.html`，填入後端 API 網址與 GCS 路徑。

---

## OAuth 同意畫面設定指南

若專案會使用 **Google Sheets** 或 **Google Drive**（例如 GAS 寫入試算表、讀取檔案），需在 GCP 設定 OAuth 同意畫面並加入對應 Scopes，才能讓 GAS 或應用程式存取使用者的試算表與雲端硬碟。

### 1. 在 GCP Console 開啟 OAuth 同意畫面

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 選取正確的 **專案**（左上角專案名稱下拉）。
3. 左側選單：**「API 和服務」** → **「OAuth 同意畫面」**。  
   - 直接連結：`https://console.cloud.google.com/apis/credentials/consent?project=YOUR_PROJECT_ID`
4. 若尚未設定：
   - 選擇 **使用者類型**（內部：僅組織；外部：可開放給任何 Google 帳號）。
   - 填寫 **應用程式名稱**、**使用者支援電子郵件**、**開發人員聯絡資訊** 等必填欄位，儲存並繼續。

### 2. 需要加入的 Scopes（Sheets、Drive）

在 OAuth 同意畫面中，點選 **「編輯應用程式」** 或 **「新增或移除 Scopes」**，加入以下與 **Sheets**、**Drive** 相關的 Scopes：

| 用途 | Scope | 說明 |
|------|--------|------|
| Google Sheets 讀寫 | `https://www.googleapis.com/auth/spreadsheets` | 試算表完整存取（讀寫） |
| Google Sheets 僅讀 | `https://www.googleapis.com/auth/spreadsheets.readonly` | 僅讀試算表 |
| Google Drive 檔案存取 | `https://www.googleapis.com/auth/drive.file` | 僅存取應用程式建立的檔案 |
| Google Drive 完整存取 | `https://www.googleapis.com/auth/drive` | 雲端硬碟完整存取（謹慎使用） |

**建議**：若 GAS 只寫入/讀取試算表，至少加入 `https://www.googleapis.com/auth/spreadsheets`；若需讀寫 Drive 上的檔案，再視需求加入 `drive` 或 `drive.file`。

### 3. 將 GAS 連結至此專案編號

Google Apps Script 預設使用 Google 的共用專案；若要使用 **本專案的 OAuth 同意畫面與配額**，需將 GAS 專案連結到你的 GCP 專案編號：

1. 在 [Apps Script](https://script.google.com/) 開啟你的 GAS 專案。
2. 左側點 **「專案設定」**（齒輪圖示）。
3. 找到 **「Google Cloud Platform (GCP) 專案」**。
4. 點 **「變更專案」**，輸入你的 **GCP 專案編號**（不是專案 ID，是數字編號）。  
   - 專案編號可在 GCP Console 首頁「專案資訊」或「設定」中查看。
5. 儲存後，該 GAS 專案會使用此 GCP 專案的 OAuth 同意畫面與已啟用的 API。

完成後，使用 Sheets/Drive 相關 API 時會依上述 Scopes 要求使用者授權。

---

## GCP 基礎設施設定

執行腳本開啟 Vertex AI 與 Secret Manager API：

```bash
./setup_project.sh YOUR_PROJECT_ID
# 或
export PROJECT_ID=your-project-id
./setup_project.sh
```

需已安裝並登入 [gcloud CLI](https://cloud.google.com/sdk/docs/install)。

## 授權

依專案需求使用。
