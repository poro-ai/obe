# gcloud init 對話框引導（專案 obe-project-485614）

執行 `gcloud init` 後，請依下列步驟在對話框中操作：

---

## 1. 登入帳號

- 若提示 **「You must log in to continue. Would you like to log in (Y/n)?」**  
  → 輸入 **Y** 後按 Enter。
- 瀏覽器會開啟 Google 登入頁，請用你的 Google 帳號登入並授權。
- 授權完成後回到終端機，繼續下一步。

---

## 2. 選擇或建立設定

- 若提示 **「Pick configuration to use:」** 或 **「Choose default configuration:」**  
  → 選 **[1] default**（或 Re-initialize this configuration），按 Enter。

---

## 3. 選取專案

- 若提示 **「Pick cloud project to use:」** 或 **「Enter project id」**  
  → 選擇或輸入專案 ID：**obe-project-485614**  
  （若清單中有 `obe-project-485614` 請選該項；若為輸入欄位則直接輸入。）

---

## 4. 完成

- 看到 **「Your Google Cloud SDK is configured and ready to use!」** 即完成。
- 接著在終端機執行：  
  `./setup_project.sh obe-project-485614`（或 `bash setup_project.sh obe-project-485614`）。
