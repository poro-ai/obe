# 本機 gcloud 權限修復與 GCP 環境初始化指南

## 權限診斷結果

- **`gcloud config list`**：可讀取設定（帳號為 `roger.yct@gmail.com`），但會出現 log 目錄權限警告。
- **寫入設定**（例如 `gcloud config set project`）：失敗，錯誤為 **Unable to create private file ... credentials.db**（存取被拒）。
- **原因**：gcloud 需對 `C:\Users\FH4\AppData\Roaming\gcloud` 有寫入權限，目前執行環境無法寫入。

**結論**：請在 **本機終端機以系統管理員身分** 執行下列步驟，完成權限修復與 GCP 初始化。

---

## 步驟一：權限修復（以管理員身分執行一次）

1. **以系統管理員身分開啟 PowerShell**  
   右鍵「開始」→「終端機 (系統管理員)」或「Windows PowerShell (系統管理員)」。

2. **執行 gcloud 初始化（建立/修復設定目錄）**  
   ```powershell
   gcloud init
   ```
   - 若提示登入，選擇 **Y** 並在瀏覽器完成登入。
   - 若提示選擇專案，可先選 `obe-project-485614` 或稍後再設。

3. **設定專案**  
   ```powershell
   gcloud config set project obe-project-485614
   ```

4. **確認設定**  
   ```powershell
   gcloud config list
   ```
   應看到 `project = obe-project-485614`、`account = roger.yct@gmail.com`（或你的帳號）。

---

## 步驟二：一鍵開啟 API（Cloud Functions、Cloud Build、Secret Manager）

在 **同一個管理員終端機** 中，切到專案根目錄後執行：

### Windows（PowerShell）

```powershell
cd D:\OBE-Project
.\setup_gcp.ps1 obe-project-485614
```

### macOS / Linux（或 Git Bash）

```bash
cd /path/to/OBE-Project
./setup_gcp.sh obe-project-485614
```

腳本會依序開啟：

- Cloud Functions API  
- Cloud Build API  
- Eventarc API  
- Cloud Run API  
- **Secret Manager API**

---

## 步驟三：驗證部署權限（Application Default 存取）

確保目前身分具備雲端存取能力（本地開發或 SDK 呼叫時會使用）：

```powershell
gcloud auth application-default login
```

- 會開啟瀏覽器，請用同一 Google 帳號授權「應用程式預設憑證」。
- 完成後執行：

```powershell
gcloud auth application-default print-access-token
```

- 若輸出一長串 token，代表 **目前身分具備雲端存取能力**，部署與本地呼叫 GCP API 可正常使用。

---

## 快速檢查清單

| 項目 | 指令 | 預期結果 |
|------|------|----------|
| 權限修復 | `gcloud init`（管理員終端） | 設定目錄可寫入 |
| 專案設定 | `gcloud config set project obe-project-485614` | 無錯誤 |
| 一鍵開啟 API | `.\setup_gcp.ps1 obe-project-485614` | 五個 API 已啟用 |
| 部署權限驗證 | `gcloud auth application-default print-access-token` | 輸出一段 token |

若某一步失敗，請確認：  
1) 是否在 **管理員 PowerShell** 執行；  
2) 是否已執行 `gcloud auth login` 與 `gcloud auth application-default login`。
