# 自動化部署架構 — 綜合檢查報告

## 1. 三大平台部署就緒狀態

| 平台 | 狀態 | 說明 |
|------|------|------|
| **GitHub Actions** | Ready | `.github/workflows/deploy.yml` 已建立，含 `--memory=1Gi`、`--timeout=540s`；需在 GitHub 設定 Secrets 後即可觸發部署。 |
| **Google Cloud (GCF)** | Pending | `main.py`、`requirements.txt` 在根目錄；`setup_gcp.sh` 已建立。本機 gcloud 因權限無法讀取設定，需在可寫入 gcloud 的環境執行驗證。 |
| **Google Apps Script (GAS)** | Ready | `.clasp.json` 含有效 scriptId；`appsscript.json` 已加入 oauthScopes（Sheets、Drive、external_request）；clasp status 同步正常。 |

---

## 2. GitHub Actions 檢查結果

### 已具備

- **檔案**：`.github/workflows/deploy.yml`
- **部署指令**：`gcloud functions deploy`，含
  - `--memory=1Gi`
  - `--timeout=540s`
  - `--gen2`、`--runtime=python311`、`--entry-point=parse_pdf`、`--trigger-http`
- **部署來源**：`--source=.`（根目錄），可抓取 `main.py` 與 `requirements.txt`

### 待完成（修復步驟）

1. **設定 GitHub Secrets**（Repository → Settings → Secrets and variables → Actions）：
   - `GCP_PROJECT_ID`：你的 GCP 專案 ID（例如 `obe-project-485614`）
   - `GCP_SA_KEY`：具備「Cloud Functions 管理員」等權限的服務帳號 JSON 金鑰內容（整份 JSON 貼上）
2. **首次部署**：可 push 到 `main` 觸發，或於 Actions 頁面手動執行「Deploy to Google Cloud Functions」workflow。

---

## 3. Google Cloud (GCF) 部署環境檢查結果

### 已具備

- **main.py**：位於專案根目錄（GCF 可抓取）
- **requirements.txt**：位於專案根目錄
- **setup_project.sh**：開啟 Vertex AI、Secret Manager API
- **setup_gcp.sh**（新建）：開啟 Cloud Functions、Cloud Build、Eventarc、Cloud Run API，並提示如何檢查已部署函式

### 本機 gcloud 檢查結果

- 執行 `gcloud config get-value project` / `gcloud config get-value account` 時，因本機 **gcloud 設定目錄權限**（`C:\Users\...\Roaming\gcloud`）無法寫入而失敗。
- **修復步驟**：
  1. 以具備該目錄寫入權限的使用者/終端機執行，或於「以系統管理員身分執行」的終端機執行一次：`gcloud init`，完成預設設定。
  2. 設定專案：`gcloud config set project YOUR_PROJECT_ID`
  3. 驗證權限與函式（若已部署）：
     - `gcloud functions list --project=YOUR_PROJECT_ID`（Gen2 可能需加 `--v2` 或依 SDK 版本）
     - `gcloud functions describe parse_pdf --region=asia-east1 --project=YOUR_PROJECT_ID`（依實際 region 調整）

### 若出現「API 未開啟」錯誤

- 執行：`./setup_gcp.sh YOUR_PROJECT_ID`
- 或手動於 [GCP Console - API 與服務 - 已啟用的 API](https://console.cloud.google.com/apis/library) 啟用：
  - Cloud Functions API
  - Cloud Build API
  - Eventarc API
  - Cloud Run API

---

## 4. Google Apps Script (GAS) 自動化檢查結果

### .clasp.json

- **scriptId**：已設定（對應目前測試環境）
- **rootDir**：`./gas`

### appsscript.json 權限範圍（Scopes）

已包含：

- **Sheets**：`https://www.googleapis.com/auth/spreadsheets`
- **Drive（應用程式建立之檔案）**：`https://www.googleapis.com/auth/drive.file`
- **外部 Fetch**：`https://www.googleapis.com/auth/script.external_request`

### clasp status（同步狀態）

- **結果**：正常
- **Tracked files**：`gas/appsscript.json`、`gas/health_check.js`、`gas/Main.js`、`gas/web_app.js`
- **Untracked files**：無

---

## 5. 缺失與修復步驟摘要

| 項目 | 狀態 | 修復步驟 |
|------|------|----------|
| GitHub Secrets | Missing（需手動設定） | 在 GitHub Repo Settings → Secrets 新增 `GCP_PROJECT_ID`、`GCP_SA_KEY`。 |
| GCF API 未開啟 | 可能 | 執行 `./setup_gcp.sh YOUR_PROJECT_ID` 或於 Console 手動啟用上述 API。 |
| gcloud 本機權限 | Pending | 修正 gcloud 設定目錄寫入權限後執行 `gcloud init` 與 `gcloud config set project`。 |
| GAS scriptId | Ready | 已對應測試環境；若更換專案請更新 `.clasp.json`。 |

---

*報告產生自專案自動化部署架構檢查。*
