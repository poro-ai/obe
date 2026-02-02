# 商品主檔快速開始指南

## 🚀 快速開始（5 分鐘）

### 步驟 1: 開啟 Apps Script 編輯器

1. 前往 [Google Apps Script](https://script.google.com)
2. 開啟你的 OBE 專案（或使用 `clasp open` 指令）

### 步驟 2: 執行初始化

在 Apps Script 編輯器中：

1. 選擇檔案：`test_product_master.js`
2. 選擇函式：`quickStart`
3. 點擊「執行」按鈕 ▶️
4. 首次執行需要授權，請點擊「審查權限」並授權

### 步驟 3: 查看結果

執行完成後：

1. 點擊「執行記錄」查看輸出
2. 複製試算表 URL
3. 在瀏覽器開啟試算表

**完成！** 你現在有一個包含範例資料的商品主檔了。

## 📁 檔案說明

| 檔案 | 說明 |
|------|------|
| `product_master.js` | 商品主檔核心功能（CRUD API） |
| `test_product_master.js` | 測試腳本與範例程式碼 |
| `README_PRODUCT_MASTER.md` | 本說明文件 |

## 🔧 可用函式

### 初始化

```javascript
// 建立商品主檔試算表（只需執行一次）
createProductMasterSheet()

// 快速開始（建立試算表 + 新增範例資料）
quickStart()

// 測試環境
quickStart({ env: 'test' })
```

### 新增商品

```javascript
// 新增單一商品
addProduct({
  category: '文具用品',
  supplier_name: 'ABC 公司',
  product_name: '多功能筆記本',
  cost_rmb: 15.50
})

// 批量匯入商品
importProducts([
  { product_name: '商品 A', cost_rmb: 10.00 },
  { product_name: '商品 B', cost_rmb: 20.00 }
])
```

### 查詢商品

```javascript
// 查詢所有商品
searchProducts()

// 依類別查詢
searchProducts({ category: '文具用品' })

// 依供應商查詢
searchProducts({ supplier_name: 'ABC' })

// 依價格區間查詢
searchProducts({ minPrice: 10, maxPrice: 50 })
```

### 取得試算表 URL

```javascript
getProductMasterSheetUrl()
```

## 🧪 測試函式

在 `test_product_master.js` 中提供了多個測試函式：

| 函式 | 說明 |
|------|------|
| `quickStart()` | **推薦** 快速建立商品主檔並新增範例資料 |
| `runAllTests()` | 執行所有測試 |
| `test_createProductMasterSheet()` | 測試建立試算表 |
| `test_addProduct()` | 測試新增單一商品 |
| `test_importProducts()` | 測試批量匯入 |
| `test_searchAllProducts()` | 測試查詢所有商品 |
| `test_searchByCategory()` | 測試依類別查詢 |
| `test_searchByPriceRange()` | 測試依價格查詢 |
| `test_getProductMasterSheetUrl()` | 測試取得 URL |

## 📊 商品主檔欄位

### 基本資訊

- **系統編號** (product_id): 自動產生，格式 `PROD-XXXXXXXX`
- **類別** (category): 下拉選單（文具用品、3C 配件等）
- **圖片 URL** (images): GCS 圖片網址，多張以逗號分隔
- **原文 URL** (raw_text_url): 整份文件原始文字的 GCS .txt URL，供比對校正用
- **供應商名稱** (supplier_name)
- **供應商產品編號** (supplier_sku)
- **產品名稱** (product_name)
- **包裝方式** (package_type): 下拉選單（開窗盒、彩盒等）

### 成本與規格

- **單價 RMB** (cost_rmb): **機密資訊**
- **基本毛利** (default_margin): 預設 0.20 (20%)
- **CNF 報價** (cnf_price)
- **外箱尺寸** (box_l, box_w, box_h): 單位公分
- **裝箱量** (pcs_per_carton)
- **內盒數量** (inner_box_qty)

### 系統欄位

- **建立時間** (created_at)
- **更新時間** (updated_at)
- **備註** (notes)

## ⚙️ 環境參數

| Script Property | 說明 |
|-----------------|------|
| PRODUCT_MASTER_SPREADSHEET_ID_PROD | 正式環境試算表 ID |
| PRODUCT_MASTER_SPREADSHEET_ID_TEST | 測試環境試算表 ID |
| OBE_ENVIRONMENT | `prod`（預設）或 `test` |

## 🔒 資料安全

**重要：成本價 (cost_rmb) 為高度機密資訊**

建議權限設定：

| 角色 | 權限 |
|------|------|
| 採購/PM | 編輯者（可見成本價） |
| 管理層 | 編輯者（可見成本價） |
| 業務/AE | 檢視者（建議建立隱藏成本欄位的副本） |

## 🖼️ 圖片管理

### 為什麼不直接存圖片？

- Google Sheets 單一儲存格最多 50,000 字元
- Base64 圖片會超過限制
- 大量圖片會拖慢試算表載入速度

### 正確做法

1. 圖片實體存放於 **GCS** (Google Cloud Storage)
2. 商品主檔只存放 **URL**
3. 路徑規則：`gs://obe-files/product-images/{product_id}/image_1.jpg`

### 圖片 URL 格式

```
# 單張圖片
gs://obe-files/product-images/PROD-12345678/image_1.jpg

# 多張圖片（逗號分隔）
gs://obe-files/product-images/PROD-12345678/image_1.jpg,gs://obe-files/product-images/PROD-12345678/image_2.jpg
```

## 🔗 與 OBE 系統整合

### 從 PDF 解析結果匯入商品（規劃中）

```javascript
// 在 web_app.js 新增 action
if (body.action === 'importToProductMaster') {
  var pages = body.pages;
  var products = _convertParsedDataToProducts(pages);
  return _jsonOutput(importProducts(products));
}
```

### 前端編輯器整合（規劃中）

在 `editor.html` 新增「匯入至商品主檔」按鈕。

## 📚 詳細文件

完整文件請參考：`docs/PRODUCT_MASTER_SETUP.md`

## 🐛 常見問題

### Q: 執行 `quickStart()` 後沒有反應？

A: 請檢查：
1. 是否已授權（首次執行需要授權）
2. 查看「執行記錄」是否有錯誤訊息
3. 確認網路連線正常

### Q: 找不到試算表？

A: 執行以下程式碼取得 URL：

```javascript
var result = getProductMasterSheetUrl();
Logger.log(result.sheetUrl);
```

### Q: 如何重新建立商品主檔？

A: 
1. 刪除舊的試算表
2. 在 Script Properties 中刪除 `PRODUCT_MASTER_SPREADSHEET_ID`
3. 重新執行 `createProductMasterSheet()`

### Q: 可以手動編輯試算表嗎？

A: 可以！試算表支援：
- 直接在儲存格編輯
- 複製貼上
- 匯入 CSV
- 使用 Google Sheets 公式

## 🚀 下一步

1. ✅ 建立商品主檔（你已完成！）
2. ⬜ 新增真實商品資料
3. ⬜ 整合 PDF/PPT/Excel 解析功能
4. ⬜ 建立前端選品 UI
5. ⬜ 實作報價引擎

## 📞 需要協助？

參考相關文件：

- PRD: `prd/禮贈品資料庫與報價系統_PRD.md`
- 詳細設定: `docs/PRODUCT_MASTER_SETUP.md`
- 系統架構: `docs/CONTEXT_FOR_ANOTHER_CHAT.md`

---

**版本**: 1.0.0  
**更新時間**: 2026-02-02
