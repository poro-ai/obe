/**
 * 商品主檔管理（Product Master Data Management）
 * 依據 PRD 第 5 節資料結構規格建立與管理商品資料庫。
 * 
 * 主要功能：
 * 1. 初始化商品主檔試算表（createProductMasterSheet）
 * 2. 新增商品（addProduct）
 * 3. 查詢商品（searchProducts）
 * 4. 匯入商品（importProducts）
 * 
 * Script Properties 設定：
 *   PRODUCT_MASTER_SPREADSHEET_ID_PROD  - 正式環境試算表 ID
 *   PRODUCT_MASTER_SPREADSHEET_ID_TEST  - 測試環境試算表 ID
 *   OBE_ENVIRONMENT                     - "prod" | "test"（選填，預設 prod）
 *   舊版相容：PRODUCT_MASTER_SPREADSHEET_ID 可作為正式環境使用
 */

/**
 * 取得商品主檔試算表 ID。
 * 優先順序：spreadsheetId 參數 > OBE_ENVIRONMENT=test > _PROD > _TEST > 舊版 PRODUCT_MASTER_SPREADSHEET_ID
 *
 * @param {Object} options 選項 { spreadsheetId?: string, env?: "prod"|"test" }
 * @return {?string} 試算表 ID，找不到時回傳 null
 */
function _getProductMasterSpreadsheetId(options) {
  options = options || {};
  if (options.spreadsheetId) return options.spreadsheetId;
  var env = options.env || _getProp('OBE_ENVIRONMENT') || 'prod';
  if (env === 'test') {
    return _getProp('PRODUCT_MASTER_SPREADSHEET_ID_TEST') || null;
  }
  return _getProp('PRODUCT_MASTER_SPREADSHEET_ID_PROD') ||
    _getProp('PRODUCT_MASTER_SPREADSHEET_ID') ||
    _getProp('PRODUCT_MASTER_SPREADSHEET_ID_TEST') ||
    null;
}

/**
 * 建立或取得商品主檔試算表。
 * 若未設定對應環境的試算表 ID 則建立新試算表。
 *
 * @param {Object} options 選項 { spreadsheetId?: string, env?: "prod"|"test" }
 * @return {Object} { success: boolean, spreadsheetId: string, sheetUrl: string, env: string, error?: string }
 */
function createProductMasterSheet(options) {
  options = options || {};
  var result = { success: false, spreadsheetId: null, sheetUrl: null, env: options.env || _getProp('OBE_ENVIRONMENT') || 'prod', error: null };
  
  try {
    var spreadsheet;
    var spreadsheetId = _getProductMasterSpreadsheetId(options);
    
    // 嘗試開啟現有試算表
    if (spreadsheetId) {
      try {
        spreadsheet = SpreadsheetApp.openById(spreadsheetId);
        result.success = true;
        result.spreadsheetId = spreadsheet.getId();
        result.sheetUrl = spreadsheet.getUrl();
        result.message = '已開啟現有商品主檔 (' + result.env + ')';
        return result;
      } catch (err) {
        // 試算表不存在或無權限，建立新的
        spreadsheet = null;
      }
    }
    
    // 建立新試算表
    var suffix = result.env === 'test' ? ' [測試]' : '';
    spreadsheet = SpreadsheetApp.create('OBE 商品主檔 (Product Master)' + suffix);
    var newId = spreadsheet.getId();
    
    if (result.env === 'test') {
      PropertiesService.getScriptProperties().setProperty('PRODUCT_MASTER_SPREADSHEET_ID_TEST', newId);
    } else {
      PropertiesService.getScriptProperties().setProperty('PRODUCT_MASTER_SPREADSHEET_ID_PROD', newId);
    }
    
    // 取得第一個工作表並重新命名
    var sheet = spreadsheet.getSheets()[0];
    sheet.setName('商品主檔');
    
    // 設定欄位標題（依據 PRD 第 5.1 與 5.2 節）
    var headers = [
      // 5.1 基本資訊
      '系統編號 (product_id)',
      '類別 (category)',
      '圖片 URL (images)',
      '原文 URL (raw_text_url)',
      '供應商名稱 (supplier_name)',
      '供應商產品編號 (supplier_sku)',
      '產品名稱 (product_name)',
      '包裝方式 (package_type)',
      
      // 5.2 成本與規格
      '單價 RMB (cost_rmb)',
      '基本毛利 (default_margin)',
      'CNF 報價 (cnf_price)',
      '外箱長 cm (box_l)',
      '外箱寬 cm (box_w)',
      '外箱高 cm (box_h)',
      '裝箱量 (pcs_per_carton)',
      '內盒數量 (inner_box_qty)',
      
      // 額外欄位
      '建立時間 (created_at)',
      '更新時間 (updated_at)',
      '備註 (notes)'
    ];
    
    // 寫入標題列
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    
    // 格式化標題列
    var headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setFontWeight('bold');
    headerRange.setBackground('#4285F4');
    headerRange.setFontColor('#FFFFFF');
    headerRange.setHorizontalAlignment('center');
    headerRange.setVerticalAlignment('middle');
    headerRange.setWrap(true);
    
    // 設定欄寬
    sheet.setColumnWidth(1, 150);  // product_id
    sheet.setColumnWidth(2, 100);  // category
    sheet.setColumnWidth(3, 250);  // images
    sheet.setColumnWidth(4, 280);  // raw_text_url
    sheet.setColumnWidth(5, 120);  // supplier_name
    sheet.setColumnWidth(6, 120);  // supplier_sku
    sheet.setColumnWidth(7, 200);  // product_name
    sheet.setColumnWidth(8, 100);  // package_type
    sheet.setColumnWidth(9, 100);  // cost_rmb
    sheet.setColumnWidth(10, 100); // default_margin
    sheet.setColumnWidth(11, 100); // cnf_price
    sheet.setColumnWidth(12, 80);  // box_l
    sheet.setColumnWidth(13, 80);  // box_w
    sheet.setColumnWidth(14, 80);  // box_h
    sheet.setColumnWidth(15, 80);  // pcs_per_carton
    sheet.setColumnWidth(16, 80);  // inner_box_qty
    sheet.setColumnWidth(17, 150); // created_at
    sheet.setColumnWidth(18, 150); // updated_at
    sheet.setColumnWidth(19, 200); // notes
    
    // 凍結標題列
    sheet.setFrozenRows(1);
    
    // 新增資料驗證（下拉選單）
    // 類別下拉選單
    var categoryValues = [
      '文具用品',
      '3C 配件',
      '生活用品',
      '環保用品',
      '運動休閒',
      '食品飲料',
      '服飾配件',
      '玩具遊戲',
      '辦公用品',
      '其他'
    ];
    var categoryRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(categoryValues, true)
      .setAllowInvalid(false)
      .build();
    sheet.getRange(2, 2, 1000, 1).setDataValidation(categoryRule);
    
    // 包裝方式下拉選單
    var packageValues = [
      '開窗盒',
      '彩盒',
      '白盒',
      '吸塑',
      '紙卡',
      '裸裝',
      '禮盒',
      '其他'
    ];
    var packageRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(packageValues, true)
      .setAllowInvalid(false)
      .build();
    sheet.getRange(2, 8, 1000, 1).setDataValidation(packageRule);
    
    // 基本毛利預設值 0.20
    sheet.getRange(2, 10, 1000, 1).setValue(0.20);
    sheet.getRange(2, 10, 1000, 1).setNumberFormat('0.00%');
    
    // 數字格式設定
    sheet.getRange(2, 9, 1000, 1).setNumberFormat('#,##0.00');  // cost_rmb
    sheet.getRange(2, 11, 1000, 1).setNumberFormat('#,##0.00'); // cnf_price
    sheet.getRange(2, 12, 1000, 3).setNumberFormat('#,##0.00'); // box_l, box_w, box_h
    sheet.getRange(2, 15, 1000, 2).setNumberFormat('#,##0');    // pcs_per_carton, inner_box_qty
    
    // 新增範例資料（第一筆）
    var now = new Date().toISOString();
    var exampleData = [
      'PROD-' + Utilities.getUuid().slice(0, 8).toUpperCase(),  // product_id
      '文具用品',                                                // category
      '',                                                       // images (空白，待上傳)
      '',                                                       // raw_text_url (GCS 原文 URL，供比對校正)
      '範例供應商',                                              // supplier_name
      'SKU-001',                                                // supplier_sku
      '範例商品 - 多功能筆記本',                                  // product_name
      '彩盒',                                                   // package_type
      15.50,                                                    // cost_rmb
      0.20,                                                     // default_margin
      18.00,                                                    // cnf_price
      30.0,                                                     // box_l
      25.0,                                                     // box_w
      20.0,                                                     // box_h
      50,                                                       // pcs_per_carton
      10,                                                       // inner_box_qty
      now,                                                      // created_at
      now,                                                      // updated_at
      '這是範例資料，可直接修改或刪除'                            // notes
    ];
    sheet.getRange(2, 1, 1, exampleData.length).setValues([exampleData]);
    
    // 新增說明工作表
    var instructionSheet = spreadsheet.insertSheet('使用說明');
    var instructions = [
      ['OBE 商品主檔使用說明'],
      [''],
      ['一、欄位說明'],
      ['1. 系統編號 (product_id): 自動產生的唯一識別碼，格式 PROD-XXXXXXXX'],
      ['2. 類別 (category): 商品分類，可從下拉選單選擇'],
      ['3. 圖片 URL (images): 商品圖片的 GCS URL，多張圖片以逗號分隔'],
      ['4. 原文 URL (raw_text_url): 整份文件的原始文字存放於 GCS 的 .txt 檔 URL，供使用者與提取資料比對校正'],
      ['5. 供應商名稱 (supplier_name): 供應商公司名稱'],
      ['6. 供應商產品編號 (supplier_sku): 供應商提供的產品編號'],
      ['7. 產品名稱 (product_name): 商品完整名稱'],
      ['8. 包裝方式 (package_type): 包裝類型，可從下拉選單選擇'],
      ['9. 單價 RMB (cost_rmb): 人民幣成本價（機密資訊）'],
      ['10. 基本毛利 (default_margin): 預設毛利率，預設 20%'],
      ['11. CNF 報價 (cnf_price): CNF (成本加運費) 報價'],
      ['12-14. 外箱尺寸 (box_l/w/h): 外箱長寬高，單位公分'],
      ['15. 裝箱量 (pcs_per_carton): 每箱裝幾件商品'],
      ['16. 內盒數量 (inner_box_qty): 每箱內有幾個內盒'],
      ['17-18. 建立/更新時間: 自動記錄時間戳記'],
      ['19. 備註 (notes): 其他補充說明'],
      [''],
      ['二、資料安全'],
      ['• 成本價 (cost_rmb) 為高度機密資訊，請妥善管理試算表權限'],
      ['• 建議僅開放給採購/PM 與管理層完整編輯權限'],
      ['• 業務/AE 可考慮建立「唯讀檢視」或「隱藏成本欄位」的副本'],
      [''],
      ['三、圖片管理'],
      ['• 圖片實體存放於 GCS (Google Cloud Storage)'],
      ['• 此欄位僅存放圖片 URL，不直接存放圖片本體'],
      ['• 多張圖片 URL 以逗號分隔，例如：'],
      ['  gs://obe-files/product-images/PROD-001/image1.jpg,gs://obe-files/product-images/PROD-001/image2.jpg'],
      [''],
      ['四、原文 URL（比對校正用）'],
      ['• 整份文件的原始文字（不含圖片）存於 GCS .txt 檔'],
      ['• 此欄位存放 URL，例如：gs://obe-files/raw-text/{doc_id}/full_text.txt'],
      ['• 匯入時將原文上傳 GCS 並填寫 URL，供使用者與提取資料比對校正'],
      [''],
      ['五、匯入資料'],
      ['• 可從 PDF/PPT/Excel 解析後匯入'],
      ['• 使用 OBE 系統的「商品匯入」功能'],
      ['• 或直接在此試算表手動新增'],
      [''],
      ['六、注意事項'],
      ['• 請勿刪除標題列（第一列）'],
      ['• 系統編號 (product_id) 必須唯一，建議使用系統自動產生'],
      ['• 數字欄位請輸入純數字，不要加單位或貨幣符號'],
      ['• 基本毛利欄位為百分比格式，0.20 表示 20%']
    ];
    instructionSheet.getRange(1, 1, instructions.length, 1).setValues(instructions);
    instructionSheet.getRange(1, 1).setFontSize(14).setFontWeight('bold');
    instructionSheet.getRange(3, 1).setFontWeight('bold');
    instructionSheet.setColumnWidth(1, 800);
    
    result.success = true;
    result.spreadsheetId = spreadsheet.getId();
    result.sheetUrl = spreadsheet.getUrl();
    result.message = '商品主檔試算表建立成功';
    
    return result;
    
  } catch (err) {
    result.error = err.toString();
    return result;
  }
}

/**
 * 新增單一商品到商品主檔。
 *
 * @param {Object} product 商品資料物件（可含 raw_text_url）
 * @param {Object} options 選項 { spreadsheetId?: string, env?: "prod"|"test" }
 * @return {Object} { success: boolean, productId: string, error?: string }
 */
function addProduct(product, options) {
  var result = { success: false, productId: null, error: null };
  
  try {
    var spreadsheetId = _getProductMasterSpreadsheetId(options);
    if (!spreadsheetId) {
      result.error = '商品主檔尚未建立，請先執行 createProductMasterSheet() 並設定 PRODUCT_MASTER_SPREADSHEET_ID_PROD 或 _TEST';
      return result;
    }
    
    var spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    var sheet = spreadsheet.getSheetByName('商品主檔');
    if (!sheet) {
      result.error = '找不到「商品主檔」工作表';
      return result;
    }
    
    // 產生系統編號
    var productId = product.product_id || ('PROD-' + Utilities.getUuid().slice(0, 8).toUpperCase());
    var now = new Date().toISOString();
    
    // 準備資料列
    var rowData = [
      productId,
      product.category || '',
      product.images || '',
      product.raw_text_url || '',
      product.supplier_name || '',
      product.supplier_sku || '',
      product.product_name || '',
      product.package_type || '',
      product.cost_rmb || 0,
      product.default_margin || 0.20,
      product.cnf_price || 0,
      product.box_l || 0,
      product.box_w || 0,
      product.box_h || 0,
      product.pcs_per_carton || 0,
      product.inner_box_qty || 0,
      now,
      now,
      product.notes || ''
    ];
    
    // 新增到最後一列
    sheet.appendRow(rowData);
    
    result.success = true;
    result.productId = productId;
    
    return result;
    
  } catch (err) {
    result.error = err.toString();
    return result;
  }
}

/**
 * 批量匯入商品（從解析結果或其他來源）。
 *
 * @param {Array} products 商品陣列（可含 raw_text_url）
 * @param {Object} options 選項 { spreadsheetId?: string, env?: "prod"|"test" }
 * @return {Object} { success: boolean, count: number, errors: Array, error?: string }
 */
function importProducts(products, options) {
  var result = { success: false, count: 0, errors: [], error: null };
  
  try {
    if (!products || !Array.isArray(products) || products.length === 0) {
      result.error = '商品陣列為空或格式錯誤';
      return result;
    }
    
    var successCount = 0;
    var errors = [];
    
    for (var i = 0; i < products.length; i++) {
      var addResult = addProduct(products[i], options);
      if (addResult.success) {
        successCount++;
      } else {
        errors.push({
          index: i,
          product: products[i].product_name || 'Unknown',
          error: addResult.error
        });
      }
    }
    
    result.success = successCount > 0;
    result.count = successCount;
    result.errors = errors;
    
    if (errors.length > 0) {
      result.error = '部分商品匯入失敗，成功 ' + successCount + ' 筆，失敗 ' + errors.length + ' 筆';
    }
    
    return result;
    
  } catch (err) {
    result.error = err.toString();
    return result;
  }
}

/**
 * 查詢商品（支援篩選條件）。
 *
 * @param {Object} filtersOrOptions 篩選條件 { category?, supplier_name?, minPrice?, maxPrice? } 或第二參數為 options 時此為 filters
 * @param {Object} optionsOrNull 選項 { spreadsheetId?: string, env?: "prod"|"test" }
 * @return {Object} { success: boolean, products: Array, count: number, error?: string }
 */
function searchProducts(filtersOrOptions, optionsOrNull) {
  var result = { success: false, products: [], count: 0, error: null };
  
  try {
    var filters = filtersOrOptions;
    var options = optionsOrNull;
    
    var spreadsheetId = _getProductMasterSpreadsheetId(options);
    if (!spreadsheetId) {
      result.error = '商品主檔尚未建立';
      return result;
    }
    
    var spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    var sheet = spreadsheet.getSheetByName('商品主檔');
    if (!sheet) {
      result.error = '找不到「商品主檔」工作表';
      return result;
    }
    
    var data = sheet.getDataRange().getValues();
    var headers = data[0];
    var products = [];
    
    // 從第二列開始（跳過標題）
    for (var i = 1; i < data.length; i++) {
      var row = data[i];
      
      // 跳過空白列
      if (!row[0]) continue;
      
      var product = {
        product_id: row[0],
        category: row[1],
        images: row[2],
        raw_text_url: row[3] || '',
        supplier_name: row[4],
        supplier_sku: row[5],
        product_name: row[6],
        package_type: row[7],
        cost_rmb: row[8],
        default_margin: row[9],
        cnf_price: row[10],
        box_l: row[11],
        box_w: row[12],
        box_h: row[13],
        pcs_per_carton: row[14],
        inner_box_qty: row[15],
        created_at: row[16],
        updated_at: row[17],
        notes: row[18]
      };
      
      // 套用篩選條件
      if (filters) {
        if (filters.category && product.category !== filters.category) continue;
        if (filters.supplier_name && product.supplier_name.indexOf(filters.supplier_name) === -1) continue;
        if (filters.minPrice && product.cost_rmb < filters.minPrice) continue;
        if (filters.maxPrice && product.cost_rmb > filters.maxPrice) continue;
      }
      
      products.push(product);
    }
    
    result.success = true;
    result.products = products;
    result.count = products.length;
    
    return result;
    
  } catch (err) {
    result.error = err.toString();
    return result;
  }
}

/**
 * 取得商品主檔試算表 URL（供前端開啟）。
 *
 * @param {Object} options 選項 { spreadsheetId?: string, env?: "prod"|"test" }
 * @return {Object} { success: boolean, sheetUrl: string, env?: string, error?: string }
 */
function getProductMasterSheetUrl(options) {
  var result = { success: false, sheetUrl: null, error: null };
  
  try {
    var spreadsheetId = _getProductMasterSpreadsheetId(options);
    if (!spreadsheetId) {
      result.error = '商品主檔尚未建立';
      return result;
    }
    
    var spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    result.success = true;
    result.sheetUrl = spreadsheet.getUrl();
    
    return result;
    
  } catch (err) {
    result.error = err.toString();
    return result;
  }
}
