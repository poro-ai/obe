/**
 * 商品主檔測試腳本
 * 用於快速測試商品主檔相關功能
 */

/**
 * 測試 1: 建立商品主檔試算表
 * 執行此函式會建立新的商品主檔試算表
 */
function test_createProductMasterSheet() {
  Logger.log('=== 測試：建立商品主檔試算表 ===');
  
  var result = createProductMasterSheet();
  
  Logger.log('結果：' + JSON.stringify(result, null, 2));
  
  if (result.success) {
    Logger.log('✅ 成功！');
    Logger.log('試算表 ID: ' + result.spreadsheetId);
    Logger.log('試算表 URL: ' + result.sheetUrl);
    Logger.log('');
    Logger.log('請開啟以下網址查看商品主檔：');
    Logger.log(result.sheetUrl);
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 測試 2: 新增單一商品
 */
function test_addProduct() {
  Logger.log('=== 測試：新增單一商品 ===');
  
  var product = {
    category: '3C 配件',
    supplier_name: '測試供應商 A',
    supplier_sku: 'TEST-SKU-001',
    product_name: '無線藍牙耳機',
    package_type: '彩盒',
    cost_rmb: 45.00,
    default_margin: 0.25,
    cnf_price: 52.00,
    box_l: 40.0,
    box_w: 30.0,
    box_h: 25.0,
    pcs_per_carton: 20,
    inner_box_qty: 4,
    notes: '熱銷商品，庫存充足'
  };
  
  var result = addProduct(product);
  
  Logger.log('結果：' + JSON.stringify(result, null, 2));
  
  if (result.success) {
    Logger.log('✅ 成功！商品 ID: ' + result.productId);
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 測試 3: 批量新增商品
 */
function test_importProducts() {
  Logger.log('=== 測試：批量匯入商品 ===');
  
  var products = [
    {
      category: '文具用品',
      supplier_name: '文具批發商',
      supplier_sku: 'STAT-001',
      product_name: '多功能筆記本 A5',
      package_type: '彩盒',
      cost_rmb: 12.50,
      default_margin: 0.20,
      box_l: 25.0,
      box_w: 20.0,
      box_h: 15.0,
      pcs_per_carton: 100,
      notes: '環保材質'
    },
    {
      category: '生活用品',
      supplier_name: '生活用品供應商',
      supplier_sku: 'LIFE-002',
      product_name: '不鏽鋼保溫杯 500ml',
      package_type: '禮盒',
      cost_rmb: 28.00,
      default_margin: 0.30,
      cnf_price: 32.00,
      box_l: 35.0,
      box_w: 30.0,
      box_h: 28.0,
      pcs_per_carton: 30,
      inner_box_qty: 6,
      notes: '316 不鏽鋼，可客製化雷雕'
    },
    {
      category: '環保用品',
      supplier_name: '綠色環保',
      supplier_sku: 'ECO-003',
      product_name: '環保購物袋',
      package_type: '裸裝',
      cost_rmb: 5.80,
      default_margin: 0.20,
      box_l: 40.0,
      box_w: 30.0,
      box_h: 20.0,
      pcs_per_carton: 200,
      raw_text_url: 'gs://obe-files/raw-text/eco-003/source.txt',
      notes: '可折疊，多色可選'
    }
  ];
  
  var result = importProducts(products);
  
  Logger.log('結果：' + JSON.stringify(result, null, 2));
  
  if (result.success) {
    Logger.log('✅ 成功匯入 ' + result.count + ' 筆商品');
    if (result.errors.length > 0) {
      Logger.log('⚠️ 有 ' + result.errors.length + ' 筆失敗');
      Logger.log('失敗項目：' + JSON.stringify(result.errors, null, 2));
    }
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 測試 4: 查詢所有商品
 */
function test_searchAllProducts() {
  Logger.log('=== 測試：查詢所有商品 ===');
  
  var result = searchProducts();
  
  if (result.success) {
    Logger.log('✅ 查詢成功，共找到 ' + result.count + ' 筆商品');
    Logger.log('');
    Logger.log('商品列表：');
    for (var i = 0; i < result.products.length; i++) {
      var p = result.products[i];
      Logger.log((i + 1) + '. ' + p.product_name + ' (' + p.category + ') - RMB ' + p.cost_rmb);
    }
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 測試 5: 依類別查詢商品
 */
function test_searchByCategory() {
  Logger.log('=== 測試：依類別查詢商品 ===');
  
  var category = '文具用品';
  var result = searchProducts({ category: category });
  
  if (result.success) {
    Logger.log('✅ 查詢成功，類別「' + category + '」共找到 ' + result.count + ' 筆商品');
    for (var i = 0; i < result.products.length; i++) {
      var p = result.products[i];
      Logger.log((i + 1) + '. ' + p.product_name + ' - RMB ' + p.cost_rmb);
    }
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 測試 6: 依價格區間查詢商品
 */
function test_searchByPriceRange() {
  Logger.log('=== 測試：依價格區間查詢商品 ===');
  
  var minPrice = 10;
  var maxPrice = 30;
  var result = searchProducts({ minPrice: minPrice, maxPrice: maxPrice });
  
  if (result.success) {
    Logger.log('✅ 查詢成功，價格區間 RMB ' + minPrice + ' - ' + maxPrice + ' 共找到 ' + result.count + ' 筆商品');
    for (var i = 0; i < result.products.length; i++) {
      var p = result.products[i];
      Logger.log((i + 1) + '. ' + p.product_name + ' - RMB ' + p.cost_rmb);
    }
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 測試 7: 取得商品主檔 URL
 */
function test_getProductMasterSheetUrl() {
  Logger.log('=== 測試：取得商品主檔 URL ===');
  
  var result = getProductMasterSheetUrl();
  
  if (result.success) {
    Logger.log('✅ 成功！');
    Logger.log('試算表 URL: ' + result.sheetUrl);
  } else {
    Logger.log('❌ 失敗：' + result.error);
  }
}

/**
 * 完整測試流程
 * 依序執行所有測試
 */
function runAllTests() {
  Logger.log('========================================');
  Logger.log('開始執行商品主檔完整測試');
  Logger.log('========================================');
  Logger.log('');
  
  // 測試 1: 建立商品主檔
  test_createProductMasterSheet();
  Logger.log('');
  Logger.log('----------------------------------------');
  Logger.log('');
  
  // 等待 2 秒
  Utilities.sleep(2000);
  
  // 測試 2: 新增單一商品
  test_addProduct();
  Logger.log('');
  Logger.log('----------------------------------------');
  Logger.log('');
  
  // 測試 3: 批量匯入
  test_importProducts();
  Logger.log('');
  Logger.log('----------------------------------------');
  Logger.log('');
  
  // 測試 4: 查詢所有商品
  test_searchAllProducts();
  Logger.log('');
  Logger.log('----------------------------------------');
  Logger.log('');
  
  // 測試 5: 依類別查詢
  test_searchByCategory();
  Logger.log('');
  Logger.log('----------------------------------------');
  Logger.log('');
  
  // 測試 6: 依價格查詢
  test_searchByPriceRange();
  Logger.log('');
  Logger.log('----------------------------------------');
  Logger.log('');
  
  // 測試 7: 取得 URL
  test_getProductMasterSheetUrl();
  Logger.log('');
  
  Logger.log('========================================');
  Logger.log('所有測試執行完畢');
  Logger.log('========================================');
}

/**
 * 快速開始：建立商品主檔並新增範例資料
 * 這是最常用的函式，一次完成初始化
 *
 * @param {Object} options 選項 { env?: "prod"|"test" }，例如 quickStart({ env: 'test' }) 建立測試環境
 */
function quickStart(options) {
  options = options || {};
  Logger.log('========================================');
  Logger.log('快速開始：建立商品主檔' + (options.env === 'test' ? ' [測試環境]' : ''));
  Logger.log('========================================');
  Logger.log('');
  
  // 步驟 1: 建立商品主檔
  Logger.log('步驟 1/2: 建立商品主檔試算表...');
  var createResult = createProductMasterSheet(options);
  
  if (!createResult.success) {
    Logger.log('❌ 建立失敗：' + createResult.error);
    return;
  }
  
  Logger.log('✅ 商品主檔建立成功！');
  Logger.log('試算表 URL: ' + createResult.sheetUrl);
  Logger.log('');
  
  // 等待 2 秒
  Utilities.sleep(2000);
  
  // 步驟 2: 新增範例商品
  Logger.log('步驟 2/2: 新增範例商品...');
  
  var exampleProducts = [
    {
      category: '3C 配件',
      supplier_name: 'Tech Supply Co.',
      supplier_sku: 'TECH-001',
      product_name: '無線藍牙耳機 TWS',
      package_type: '彩盒',
      cost_rmb: 45.00,
      default_margin: 0.25,
      cnf_price: 52.00,
      box_l: 40.0,
      box_w: 30.0,
      box_h: 25.0,
      pcs_per_carton: 20,
      inner_box_qty: 4,
      notes: '藍牙 5.0，續航 6 小時'
    },
    {
      category: '文具用品',
      supplier_name: '文具批發商',
      supplier_sku: 'STAT-002',
      product_name: '多功能筆記本套裝',
      package_type: '禮盒',
      cost_rmb: 18.50,
      default_margin: 0.20,
      box_l: 30.0,
      box_w: 25.0,
      box_h: 20.0,
      pcs_per_carton: 50,
      notes: '含筆記本 + 原子筆 + 便利貼'
    },
    {
      category: '生活用品',
      supplier_name: '優質生活',
      supplier_sku: 'LIFE-003',
      product_name: '316 不鏽鋼保溫杯 500ml',
      package_type: '禮盒',
      cost_rmb: 32.00,
      default_margin: 0.30,
      cnf_price: 36.00,
      box_l: 35.0,
      box_w: 30.0,
      box_h: 28.0,
      pcs_per_carton: 30,
      inner_box_qty: 6,
      notes: '316 不鏽鋼，保溫 12 小時，可雷雕'
    }
  ];
  
  var importResult = importProducts(exampleProducts, options);
  
  if (importResult.success) {
    Logger.log('✅ 成功新增 ' + importResult.count + ' 筆範例商品');
  } else {
    Logger.log('⚠️ 範例商品新增失敗：' + importResult.error);
  }
  
  Logger.log('');
  Logger.log('========================================');
  Logger.log('✅ 完成！商品主檔已準備就緒');
  Logger.log('========================================');
  Logger.log('');
  Logger.log('請開啟以下網址查看商品主檔：');
  Logger.log(createResult.sheetUrl);
  Logger.log('');
  Logger.log('提示：');
  Logger.log('- 商品主檔已包含範例資料，可直接修改或刪除');
  Logger.log('- 使用 addProduct() 新增更多商品');
  Logger.log('- 使用 searchProducts() 查詢商品');
  Logger.log('- 查看「使用說明」工作表了解更多資訊');
}
