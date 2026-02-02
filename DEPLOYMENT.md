# 部署備忘：GitHub Secrets 與連結

## GitHub Actions 部署 GCF + GAS

- **push 到 main 時**：`.github/workflows/deploy.yml` 會依序執行：
  1. **Deploy Cloud Function**：部署 **parse_pdf** 到 GCP。
  2. **Deploy GAS**：以 clasp push 將 **gas/** 同步到 Google Apps Script（需先設定 `CLASP_JSON`、`CLASPRC_JSON` 兩個 secrets，見下表）。
- 若未設定 GAS 相關 secrets，`deploy-gas` job 會失敗；此時仍可僅在本機執行 **`npx @google/clasp push`** 手動同步 GAS。

**標準流程（commit + clasp + push）**：每次改動後建議一併執行 Git 提交、GAS 推送、GitHub 推送：
```bash
# 一鍵（Windows PowerShell）
.\scripts\commit-push-and-clasp.ps1 "你的 commit 訊息"

# 一鍵（macOS/Linux）
./scripts/commit-push-and-clasp.sh "你的 commit 訊息"

# 或分步
git add -A && git commit -m "..." && npx @google/clasp push && git push origin main
```
助理在執行「commit and push」時會一併執行 clasp push。

---

## 無法代為開啟瀏覽器

Cursor 無法代你開啟瀏覽器。請自行在瀏覽器開啟下列網址：

### GitHub Repository — Secrets 設定頁面

```
https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
```

請將 `YOUR_USERNAME`、`YOUR_REPO` 換成你的 GitHub 使用者名稱與倉庫名稱。  
若已設定 `origin` 遠端，可從專案根目錄執行 `git remote get-url origin` 取得倉庫網址，再依此推得上述設定頁面。

---

## 接下來要填入的 Secrets 名稱（備忘）

在 **Settings → Secrets and variables → Actions** 中新增以下 Repository secrets：

| Secret 名稱 | 說明 | 範例／格式 |
|-------------|------|------------|
| **GCP_PROJECT_ID** | GCP 專案 ID，用於部署 Cloud Functions | 例如：`obe-project-485614` |
| **GCP_SA_KEY** | 具備 Cloud Functions 部署權限的服務帳號 **整份 JSON 金鑰內容** | 從 GCP Console 建立服務帳號並下載 JSON，將檔案內容整段貼上 |
| **GEMINI_API_KEY** | Gemini API 金鑰，供 GCF 呼叫 File API 上傳／解析 PDF | 從 [Google AI Studio](https://aistudio.google.com/apikey) 取得，貼上字串 |
| **CLASP_JSON** | （GAS 用）本機 `.clasp.json` 內容，供 CI 執行 clasp push | 單行 JSON，例：`{"scriptId":"你的 Apps Script 專案 ID","rootDir":"./gas"}` |
| **CLASPRC_JSON** | （GAS 用）本機 clasp login 後 `~/.clasprc.json` 的**完整內容** | 在本機執行 `clasp login` 後，將 `~/.clasprc.json`（或 Windows `%USERPROFILE%\.clasprc.json`）整份貼上 |

---

## GAS 上傳 GCS 時出現 403（Permission denied）

若 GAS doPost 回傳錯誤類似：

```
GCS upload failed: 403 ... does not have storage.objects.create access ...
Permission 'storage.objects.create' denied on resource
```

表示 **GAS 使用的服務帳號**（GAS 指令碼內容中的 `GCP_SA_CLIENT_EMAIL` / `GCP_SA_PRIVATE_KEY`）**沒有**在 GCS bucket（預設 `obe-files`）上建立物件的權限。

**修復**：在 GCP 為該服務帳號授予 bucket 的 **Storage Object Creator**（或 **Storage Admin**）。

```bash
# 將 YOUR_SA_EMAIL 換成 GAS 用的服務帳號 email（例如 github-deploy-sa@obe-project-485614.iam.gserviceaccount.com）
# 將 BUCKET 換成實際 bucket 名稱（例如 obe-files）

gcloud storage buckets add-iam-policy-binding gs://BUCKET \
  --member="serviceAccount:YOUR_SA_EMAIL" \
  --role="roles/storage.objectCreator" \
  --project=obe-project-485614
```

或於 **GCP Console → Cloud Storage → 選擇 bucket → 權限** 新增成員，加入該服務帳號並指派 **Storage Object Creator**。

---

## 參考

- 部署流程與狀態：`docs/DEPLOYMENT_STATUS.md`
- 工作流程定義：`.github/workflows/deploy.yml`
