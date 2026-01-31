# 部署備忘：GitHub Secrets 與連結

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
