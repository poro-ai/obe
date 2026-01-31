# gcloud init 與環境建置步驟（PowerShell 已設 RemoteSigned）

## 1. 執行 gcloud init（對話框引導）

在本機 **PowerShell** 或 **命令提示字元** 執行：

```powershell
gcloud init
```

### 對話框中請依序操作：

1. **Re-run gcloud init? (y/N)**  
   → 若為首次或要重新設定，輸入 **Y**。

2. **Choose the account to use**  
   → 選擇要使用的帳號（例如 `roger.yct@gmail.com`），或選 **「Log in with a new account」** 在瀏覽器登入。

3. **Pick cloud project to use**  
   → 選擇 **「Enter a project id」**，輸入：**obe-project-485614**。  
   （若清單中已有 `obe-project-485614` 可直接選取。）

4. 完成後會顯示目前使用的帳號與專案。

---

## 2. 啟用 API（等同 ./setup_project.sh）

### 若本機有 Git Bash，可執行：

```bash
./setup_project.sh obe-project-485614
```

### 或在 PowerShell 手動執行：

```powershell
gcloud config set project obe-project-485614
gcloud services enable aiplatform.googleapis.com --project=obe-project-485614
gcloud services enable secretmanager.googleapis.com --project=obe-project-485614
```

會開啟 **Vertex AI** 與 **Secret Manager** API。

---

## 3. 驗證狀態

```powershell
gcloud config list
```

確認輸出中有：

- **account** = 你的 Google 帳號  
- **project** = obe-project-485614  

（若沒有 `project`，再執行一次 `gcloud config set project obe-project-485614`。）

---

## 4. config_loader.py 與 GCP 專案

`src/clients/config_loader.py` **已依環境變數設計**，無需寫死專案 ID：

- **local**：從 `.env`（python-dotenv）讀取 `GEMINI_API_KEY`、`PROJECT_ID` 等。
- **production**：專案 ID 來自 **`PROJECT_ID`** 或 **`GOOGLE_CLOUD_PROJECT`**（環境變數），再用 Secret Manager 抓金鑰。

只要在 `.env` 或雲端環境變數中設定 **PROJECT_ID=obe-project-485614**，即可對應到你的 GCP 專案。
