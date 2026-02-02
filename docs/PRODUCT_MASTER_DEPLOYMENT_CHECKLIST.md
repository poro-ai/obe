# 商品主檔部署檢查清單

## 📋 部署前檢查

### 1. 檔案確認

確認以下檔案已建立：

- [ ] `gas/product_master.js` - 核心功能
- [ ] `gas/test_product_master.js` - 測試腳本
- [ ] `gas/README_PRODUCT_MASTER.md` - 使用說明
- [ ] `docs/PRODUCT_MASTER_SETUP.md` - 詳細文件
- [ ] `docs/PRODUCT_MASTER_DEPLOYMENT_CHECKLIST.md` - 本檔案

### 2. 權限確認

確認 `gas/appsscript.json` 包含以下權限：

- [ ] `https://www.googleapis.com/auth/spreadsheets` - 操作試算表
- [ ] `https://www.googleapis.com/auth/drive.file` - 建立檔案
- [ ] `https://www.googleapis.com/auth/script.external_request` - 外部請求（未來整合用）

### 3. 依賴確認

確認 `gas/web_app.js` 中的 `_getProp()` 函式可用（商品主檔會使用）。

## 🚀 部署步驟

### 方法一：使用 clasp（推薦）

```bash
# 1. 確認在專案根目錄
cd d:\OBE-Project

# 2. 推送到 GAS
npx @google/clasp push

# 3. 開啟 Apps Script 編輯器
npx @google/clasp open
```

### 方法二：手動複製

1. 開啟 [Apps Script 編輯器](https://script.google.com)
2. 開啟 OBE 專案
3. 新增檔案：
   - `product_master.js`
   - `test_product_master.js`
4. 複製貼上程式碼
5. 儲存

## ✅ 部署後測試

### 測試 1: 快速開始（推薦）

```javascript
// 在 Apps Script 編輯器中執行
quickStart()
```

**預期結果：**
- ✅ 建立新的試算表
- ✅ 新增 3 筆範例商品
- ✅ 執行記錄顯示試算表 URL

### 測試 2: 完整測試

```javascript
// 在 Apps Script 編輯器中執行
runAllTests()
```

**預期結果：**
- ✅ 所有 7 個測試通過
- ✅ 無錯誤訊息

### 測試 3: 手動驗證

1. 開啟建立的試算表
2. 確認欄位標題正確（18 個欄位）
3. 確認範例資料存在
4. 確認「使用說明」工作表存在
5. 測試下拉選單（類別、包裝方式）
6. 測試數字格式（成本價、毛利等）

## 🔧 Script Properties 設定

部署後，系統會自動設定以下 Script Property：

| Key | Value | 說明 |
|-----|-------|------|
| `PRODUCT_MASTER_SPREADSHEET_ID` | 試算表 ID | 自動設定，無需手動 |

**查看方式：**
1. Apps Script 編輯器
2. 專案設定（齒輪圖示）
3. 指令碼內容

## 🔒 權限設定

### 商品主檔試算表權限

建立後請設定適當權限：

| 角色 | 建議權限 |
|------|---------|
| 採購/PM | 編輯者 |
| 管理層 | 編輯者 |
| 業務/AE | 檢視者（或建立隱藏成本欄位的副本） |

**設定方式：**
1. 開啟試算表
2. 點擊右上角「共用」
3. 新增人員並設定權限

## 📊 驗證清單

### 功能驗證

- [ ] 可以建立商品主檔試算表
- [ ] 可以新增單一商品
- [ ] 可以批量匯入商品
- [ ] 可以查詢所有商品
- [ ] 可以依類別查詢
- [ ] 可以依價格區間查詢
- [ ] 可以取得試算表 URL

### 資料驗證

- [ ] 系統編號格式正確（PROD-XXXXXXXX）
- [ ] 類別下拉選單正常
- [ ] 包裝方式下拉選單正常
- [ ] 基本毛利預設為 20%
- [ ] 數字格式正確（千分位、小數點）
- [ ] 時間戳記格式正確（ISO 8601）

### 試算表驗證

- [ ] 標題列格式正確（藍底白字、粗體、置中）
- [ ] 欄寬適當
- [ ] 標題列已凍結
- [ ] 使用說明工作表存在且內容完整

## 🐛 常見問題排除

### 問題 1: 執行時出現「找不到函式」錯誤

**原因：** 檔案未正確推送或儲存

**解決方式：**
1. 確認檔案已儲存
2. 重新執行 `clasp push`
3. 重新整理 Apps Script 編輯器

### 問題 2: 授權失敗

**原因：** 首次執行需要授權

**解決方式：**
1. 點擊「審查權限」
2. 選擇 Google 帳號
3. 點擊「進階」→「前往 OBE（不安全）」
4. 點擊「允許」

### 問題 3: 試算表建立失敗

**原因：** 權限不足或 Google Drive 空間不足

**解決方式：**
1. 確認 Google Drive 有足夠空間
2. 確認 `appsscript.json` 包含 `drive.file` 權限
3. 重新授權

### 問題 4: Script Property 未設定

**原因：** 首次執行失敗或權限問題

**解決方式：**
1. 手動設定 Script Property
2. 或刪除後重新執行 `createProductMasterSheet()`

## 📝 部署記錄

### 版本 1.0.0 (2026-02-02)

**新增功能：**
- ✅ 商品主檔資料結構（依據 PRD 第 5 節）
- ✅ CRUD API（建立、新增、查詢）
- ✅ 測試腳本與範例資料
- ✅ 使用說明文件

**已知限制：**
- ⚠️ 圖片上傳功能尚未實作（僅支援 URL）
- ⚠️ 更新與刪除功能尚未實作
- ⚠️ 與 PDF 解析整合尚未實作

**下一步：**
- [ ] 實作圖片上傳到 GCS
- [ ] 實作更新與刪除功能
- [ ] 整合 PDF/PPT/Excel 解析
- [ ] 建立前端選品 UI

## 🔄 更新流程

當商品主檔功能有更新時：

1. 修改 `gas/product_master.js`
2. 執行 `npx @google/clasp push`
3. 在 Apps Script 編輯器測試
4. 更新文件（如有需要）
5. 記錄版本變更

## 📞 需要協助？

如遇到問題，請檢查：

1. **執行記錄**：Apps Script 編輯器 → 執行記錄
2. **詳細文件**：`docs/PRODUCT_MASTER_SETUP.md`
3. **PRD 文件**：`prd/禮贈品資料庫與報價系統_PRD.md`
4. **系統架構**：`docs/CONTEXT_FOR_ANOTHER_CHAT.md`

---

**版本**: 1.0.0  
**更新時間**: 2026-02-02  
**負責人**: OBE Team
