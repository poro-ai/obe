# 商品主檔建立與使用指南

## 一、概述

本文件說明如何建立與使用 OBE 商品主檔（Product Master Data），用於管理禮贈品資料庫。

商品主檔是禮贈品報價系統的核心，依據 `prd/禮贈品資料庫與報價系統_PRD.md` 第 5 節資料結構規格設計。

## 二、資料結構

### 2.1 基本資訊 (Basic Info)

| 欄位代碼 | 欄位名稱 | 類型 | 說明 |
|---------|---------|------|------|
| product_id | 系統編號 | UUID | 主鍵，格式 PROD-XXXXXXXX |
| category | 類別 | String | 下拉選單（文具用品、3C 配件等） |
| images | 圖片 URL | String | GCS URL，多張以逗號分隔 |
| raw_text_url | 原文 URL | String | 整份文件原始文字存於 GCS .txt 的 URL，供比對校正用 |
| supplier_name | 供應商名稱 | String | 供應商公司名稱 |
| supplier_sku | 供應商產品編號 | String | 供應商提供的 SKU |
| product_name | 產品名稱 | String | 商品完整名稱 |
| package_type | 包裝方式 | String | 下拉選單（開窗盒、彩盒等） |

### 2.2 成本與規格 (Cost & Specs)

| 欄位代碼 | 欄位名稱 | 類型 | 說明 |
|---------|---------|------|------|
| cost_rmb | 單價 (RMB) | Decimal | **機密資訊** |
| default_margin | 基本毛利 | Decimal | 預設 0.20 (20%) |
| cnf_price | CNF 報價 | Decimal | 成本加運費報價 |
| box_l | 外箱長 (cm) | Decimal | 外箱長度 |
| box_w | 外箱寬 (cm) | Decimal | 外箱寬度 |
| box_h | 外箱高 (cm) | Decimal | 外箱高度 |
| pcs_per_carton | 裝箱量 | Int | 每箱裝幾件 |
| inner_box_qty | 內盒數量 | Int | 每箱內盒數 |

### 2.3 系統欄位

| 欄位代碼 | 欄位名稱 | 類型 | 說明 |
|---------|---------|------|------|
| created_at | 建立時間 | DateTime | ISO 8601 格式 |
| updated_at | 更新時間 | DateTime | ISO 8601 格式 |
| notes | 備註 | String | 其他補充說明 |

## 三、環境與參數設定

### 3.1 Script Properties

| Key | 說明 | 範例 |
|-----|------|------|
| PRODUCT_MASTER_SPREADSHEET_ID_PROD | 正式環境試算表 ID | 自動設定或手動填入 |
| PRODUCT_MASTER_SPREADSHEET_ID_TEST | 測試環境試算表 ID | 自動設定或手動填入 |
| OBE_ENVIRONMENT | 使用環境 | `prod`（預設）或 `test` |

**舊版相容**：若已設定 `PRODUCT_MASTER_SPREADSHEET_ID`，會作為正式環境使用。

### 3.2 環境選擇邏輯

1. 函式參數 `spreadsheetId` 或 `env` 有值時，依參數決定
2. 否則依 `OBE_ENVIRONMENT`：`test` 使用 `_TEST`，`prod` 使用 `_PROD`

## 四、建立商品主檔

### 方法一：使用 GAS 函式（推薦）

1. 開啟 Apps Script 編輯器（script.google.com）
2. 開啟 OBE 專案
3. 在「執行」選單中選擇 `quickStart`（或 `createProductMasterSheet`）
4. 授權後執行
5. 查看執行記錄取得試算表 URL

**測試環境**：執行 `quickStart({ env: 'test' })` 建立測試用試算表

### 方法二：透過 Web App API

```bash
# POST 到 GAS Web App
curl -X POST "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"action": "createProductMaster"}'
```

### 執行結果

函式會：
1. 建立名為「OBE 商品主檔 (Product Master)」的新試算表
2. 設定所有欄位與格式
3. 新增資料驗證（下拉選單）
4. 插入範例資料
5. 建立「使用說明」工作表
6. 將試算表 ID 存入 Script Properties（依 `OBE_ENVIRONMENT` 存入 `_PROD` 或 `_TEST`）

## 五、使用 API

### 5.1 新增單一商品

```javascript
var product = {
  category: '文具用品',
  supplier_name: 'ABC 公司',
  supplier_sku: 'ABC-001',
  product_name: '多功能筆記本',
  package_type: '彩盒',
  raw_text_url: 'gs://obe-files/raw-text/doc-001/full_text.txt',  // 選填，原文 URL
  cost_rmb: 15.50,
  default_margin: 0.20,
  cnf_price: 18.00,
  box_l: 30.0,
  box_w: 25.0,
  box_h: 20.0,
  pcs_per_carton: 50,
  inner_box_qty: 10,
  notes: '熱銷商品'
};

var result = addProduct(product);
// 測試環境：addProduct(product, { env: 'test' });
Logger.log(result);
// { success: true, productId: "PROD-12345678" }
```

### 5.2 批量匯入商品

```javascript
var products = [
  { product_name: '商品 A', cost_rmb: 10.00, ... },
  { product_name: '商品 B', cost_rmb: 20.00, ... },
  // ...
];

var result = importProducts(products);
Logger.log(result);
// { success: true, count: 2, errors: [] }
```

### 5.3 查詢商品

```javascript
// 查詢所有商品
var result = searchProducts();

// 依類別篩選
var result = searchProducts({ category: '文具用品' });

// 依供應商篩選
var result = searchProducts({ supplier_name: 'ABC' });

// 依價格區間篩選
var result = searchProducts({ minPrice: 10, maxPrice: 50 });

Logger.log(result);
// { success: true, products: [...], count: 10 }
```

### 5.4 取得試算表 URL

```javascript
var result = getProductMasterSheetUrl();
Logger.log(result.sheetUrl);
// https://docs.google.com/spreadsheets/d/...
```

## 六、圖片管理

### 6.1 圖片存放策略

依據 Context 文件與先前討論：

- **圖片實體**：存放於 **GCS** (Google Cloud Storage)
- **商品主檔**：僅存放 **URL**，不存放圖片本體
- **路徑規則**：`gs://obe-files/product-images/{product_id}/image_{n}.jpg`

### 6.2 為什麼不存圖片本體？

1. **儲存格限制**：Google Sheets 單一儲存格最多 50,000 字元
2. **Base64 膨脹**：圖片轉 Base64 後體積增加約 33%，容易超過限制
3. **效能問題**：大量圖片會拖慢試算表載入速度
4. **版本管理**：GCS 提供更好的圖片版本控制與 CDN 支援

### 6.3 圖片 URL 格式

```
# 單張圖片
gs://obe-files/product-images/PROD-12345678/image_1.jpg

# 多張圖片（逗號分隔）
gs://obe-files/product-images/PROD-12345678/image_1.jpg,gs://obe-files/product-images/PROD-12345678/image_2.jpg

# 或使用 HTTPS URL (Signed URL)
https://storage.googleapis.com/obe-files/product-images/PROD-12345678/image_1.jpg?X-Goog-Algorithm=...
```

### 6.4 圖片上傳流程（規劃中）

```
1. 前端選擇圖片
2. 上傳到 GCS (透過 GAS 或直接上傳)
3. 取得 GCS URL
4. 將 URL 寫入商品主檔的 images 欄位
```

## 七、原文 URL（比對校正用）

### 7.1 用途

`raw_text_url` 存放整份文件的原始文字（不含圖片），供使用者與 AI 提取的資料比對校正。

### 7.2 儲存策略

| 項目 | 做法 |
|------|------|
| 原文實體 | 存於 GCS（.txt 檔） |
| 商品主檔 | 僅存 URL |
| 格式 | 純文字，建議以 `--- 第 N 頁 ---` 分隔頁面 |

### 7.3 路徑範例

```
gs://obe-files/raw-text/{document_id}/full_text.txt
```

### 7.4 匯入流程

1. 解析 PDF/PPT/Excel 取得商品資料
2. 同時將整份原文（純文字）上傳到 GCS
3. 將取得的 GCS URL 寫入 `raw_text_url` 欄位
4. 編輯器／UI 依 URL 讀取並顯示，與提取結果並排比對

## 八、資料安全

### 8.1 權限管理

**成本價 (cost_rmb) 為高度機密資訊**，需妥善管理試算表權限：

| 角色 | 權限 | 可見欄位 |
|------|------|---------|
| 採購/PM | 編輯者 | 全部欄位（含成本價） |
| 管理層 | 編輯者 | 全部欄位（含成本價） |
| 業務/AE | 檢視者 | 建議建立「隱藏成本欄位」的副本 |

### 8.2 建立業務檢視副本

```javascript
// 複製試算表並隱藏敏感欄位
function createSalesView() {
  var masterSpreadsheet = SpreadsheetApp.openById('MASTER_SPREADSHEET_ID');
  var salesSpreadsheet = masterSpreadsheet.copy('OBE 商品主檔（業務檢視）');
  var sheet = salesSpreadsheet.getSheets()[0];
  
  // 隱藏成本價欄位（第 8 欄）
  sheet.hideColumns(8);
  
  // 設為唯讀保護
  var protection = sheet.protect().setDescription('業務檢視（唯讀）');
  protection.setWarningOnly(true);
  
  Logger.log('業務檢視已建立：' + salesSpreadsheet.getUrl());
}
```

## 九、與現有 OBE 系統整合

### 9.1 從 PDF 解析匯入商品

```javascript
// 在 web_app.js 新增 action
if (body.action === 'importToProductMaster') {
  var pages = body.pages;
  var products = _convertParsedDataToProducts(pages);
  return _jsonOutput(importProducts(products));
}

function _convertParsedDataToProducts(pages) {
  var products = [];
  for (var i = 0; i < pages.length; i++) {
    var elements = pages[i].elements || [];
    var product = {
      product_name: '',
      images: '',
      notes: ''
    };
    
    for (var j = 0; j < elements.length; j++) {
      var el = elements[j];
      if (el.type === 'image' && el.content) {
        // 將 base64 圖片上傳到 GCS，取得 URL
        // product.images = uploadImageToGcs(el.content);
      } else if (el.type === 'text') {
        product.product_name += el.content + ' ';
        product.notes += el.description + ' ';
      }
    }
    
    if (product.product_name) {
      products.push(product);
    }
  }
  return products;
}
```

### 9.2 前端編輯器整合

在 `editor.html` 新增「匯入至商品主檔」按鈕：

```javascript
async function importToProductMaster() {
  const pages = getEditedPages();
  const response = await fetch(GAS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'importToProductMaster',
      pages: pages
    })
  });
  const result = await response.json();
  if (result.success) {
    alert(`成功匯入 ${result.count} 筆商品`);
  }
}
```

## 十、後續開發

### Phase 1 (MVP) - 已完成
- ✅ 建立商品主檔資料結構
- ✅ 實作基礎 CRUD API
- ✅ 新增範例資料與使用說明

### Phase 2 - 待開發
- ⬜ 實作圖片上傳到 GCS 功能
- ⬜ 整合 PDF/PPT/Excel 解析結果自動匯入
- ⬜ 建立前端選品 UI
- ⬜ 實作搜尋與篩選 API

### Phase 3 - 待開發
- ⬜ 報價引擎與成本計算邏輯
- ⬜ Excel/PDF 報價單產出
- ⬜ 權限管理與業務檢視

## 十一、測試

### 11.1 手動測試

```javascript
// 1. 建立商品主檔
var result = createProductMasterSheet();
Logger.log(result);

// 2. 新增商品
var product = {
  category: '3C 配件',
  supplier_name: '測試供應商',
  product_name: '測試商品',
  cost_rmb: 25.00
};
var addResult = addProduct(product);
Logger.log(addResult);

// 3. 查詢商品
var searchResult = searchProducts({ category: '3C 配件' });
Logger.log(searchResult);

// 4. 取得試算表 URL
var urlResult = getProductMasterSheetUrl();
Logger.log(urlResult.sheetUrl);
```

### 11.2 單元測試（待建立）

建立 `tests/gas/test_product_master.js`：

```javascript
function testCreateProductMasterSheet() {
  var result = createProductMasterSheet();
  assert(result.success === true);
  assert(result.spreadsheetId !== null);
}

function testAddProduct() {
  var product = { product_name: 'Test Product', cost_rmb: 10.00 };
  var result = addProduct(product);
  assert(result.success === true);
  assert(result.productId.indexOf('PROD-') === 0);
}
```

## 十二、常見問題

### Q1: 如何修改類別或包裝方式的下拉選單選項？

A: 在 `product_master.js` 的 `createProductMasterSheet()` 函式中修改 `categoryValues` 或 `packageValues` 陣列。

### Q2: 如何備份商品主檔？

A: 
1. 開啟試算表
2. 檔案 → 建立副本
3. 或使用 Google Drive API 定期自動備份

### Q3: 可以匯出成 Excel 嗎？

A:
1. 開啟試算表
2. 檔案 → 下載 → Microsoft Excel (.xlsx)

### Q4: 如何處理大量商品（1000+ 筆）？

A: Google Sheets 單一工作表最多支援 1000 萬個儲存格。若商品數量超過 10 萬筆，建議：
1. 分類建立多個工作表
2. 或改用 Google Cloud SQL / Firestore

## 十三、相關文件

- PRD: `prd/禮贈品資料庫與報價系統_PRD.md`
- Context: `docs/CONTEXT_FOR_ANOTHER_CHAT.md`
- 部署說明: `DEPLOYMENT.md`

---

**更新時間**: 2026-02-02  
**版本**: 1.0.0
