# 本機 gcloud 設定與 API 開啟指南

## 檢查結果：權限不足

目前在本機執行 `gcloud config get-value project` 時出現：

- **錯誤**：無法在 `C:\Users\FH4\AppData\Roaming\gcloud` 建立設定目錄（Permission denied）。
- **原因**：gcloud 需要對該目錄的寫入權限；目前環境（例如 Cursor 內建終端或權限限制）無法寫入。

因此請在 **本機自己的終端機**（PowerShell 或 CMD，必要時「以系統管理員身分執行」）依下列步驟操作。

---

## 步驟一：修正 gcloud 並登入

在 **本機** 開啟 **PowerShell** 或 **命令提示字元**（建議以一般使用者身分先試，若仍權限錯誤再以系統管理員身分執行），依序執行：

### 1. 登入 Google Cloud

```powershell
gcloud auth login
```

- 會開啟瀏覽器，請用要使用的 Google 帳號登入並授權。
- 完成後關閉瀏覽器，回到終端機。

### 2. 設定預設專案

```powershell
gcloud config set project obe-project-485614
```

### 3. 確認設定

```powershell
gcloud config get-value project
gcloud config get-value account
```

應分別顯示 `obe-project-485614` 與你的 Google 帳號。

---

## 步驟二：開啟雲端 API（等同 ./setup_gcp.sh）

專案目錄內已提供 **Windows 版腳本**，在 **同一個本機終端機** 中，先切到專案根目錄再執行：

```powershell
cd D:\OBE-Project
.\setup_gcp.ps1 obe-project-485614
```

若偏好手動執行 gcloud，可依序執行：

```powershell
gcloud config set project obe-project-485614
gcloud services enable cloudfunctions.googleapis.com --project=obe-project-485614
gcloud services enable cloudbuild.googleapis.com --project=obe-project-485614
gcloud services enable eventarc.googleapis.com --project=obe-project-485614
gcloud services enable run.googleapis.com --project=obe-project-485614
```

完成後，Cloud Functions、Cloud Build、Eventarc、Cloud Run 等部署所需 API 即已開啟。

---

## 若仍出現「Permission denied」

1. **以系統管理員身分**開啟 PowerShell：  
   右鍵「開始」→「Windows PowerShell (系統管理員)」。
2. 再次執行：
   ```powershell
   gcloud auth login
   gcloud config set project obe-project-485614
   ```
3. 或將 gcloud 設定目錄改到有寫入權限的位置（需查 gcloud 文件設定 `CLOUDSDK_CONFIG`）。

完成上述步驟後，再於同一終端機執行 `.\setup_gcp.ps1 obe-project-485614` 即可確保雲端 API 已全數開啟。
