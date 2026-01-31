# 部署備忘：GitHub Secrets 與連結

## GitHub Actions 只部署 GCF，不部署 GAS

- **push 到 main 時**：`.github/workflows/deploy.yml` 會執行，僅部署 **Google Cloud Function (parse_pdf)** 到 GCP，不會更新 **Google Apps Script (GAS)**。
- **GAS 程式碼**（`gas/` 目錄）需在本機執行 **`npx @google/clasp push`** 才會同步到 script.google.com。
- 原因：GAS 部署需 clasp 登入與 `.clasp.json`（scriptId），該檔在 .gitignore 且 CI 無 clasp 憑證，故未納入 workflow。

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

---

## 參考

- 部署流程與狀態：`docs/DEPLOYMENT_STATUS.md`
- 工作流程定義：`.github/workflows/deploy.yml`
