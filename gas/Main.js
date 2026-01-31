/**
 * Google Slides 附加元件／容器腳本入口。
 * - onOpen()：新增選單按鈕，點擊後開啟 AI 解析側邊欄。
 * - showSidebar()：以 HtmlService 載入 sidebar.html。
 * - uploadToGcs(fileDataBase64, fileName)：將 PDF 上傳至 GCS，回傳 { bucket, objectName }。
 * - callGcfParse(bucket, objectName)：呼叫 GCF parse_pdf，回傳 { success, pages, error, count }。
 *
 * 依賴 web_app.js 的 _getProp、_uploadToGcs、_callGcfParsePdf（同一專案內可呼叫）。
 */

function onOpen() {
  SlidesApp.getUi()
    .createMenu('OBE')
    .addItem('開啟 AI 解析側邊欄', 'showSidebar')
    .addToUi();
}

/**
 * 開啟 AI 解析側邊欄，載入 gas/sidebar.html。
 */
function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('sidebar')
    .setTitle('AI 解析')
    .setWidth(320);
  SlidesApp.getUi().showSidebar(html);
}

/**
 * 將 PDF（Base64）上傳至 GCS。
 * @param {string} fileDataBase64 - PDF 的 Base64 字串（不含 data URL 前綴）
 * @param {string} fileName - 檔案名稱
 * @returns {{ bucket: string, objectName: string }} 供後續 callGcfParse 使用
 */
function uploadToGcs(fileDataBase64, fileName) {
  var bucket = _getProp('GCS_BUCKET') || 'obe-files';
  var prefix = 'uploads/' + new Date().getTime() + '_';
  var safeName = (fileName || 'upload.pdf').replace(/[^a-zA-Z0-9._-]/g, '_');
  var objectName = prefix + safeName;

  var pdfBytes = Utilities.base64Decode(fileDataBase64);
  var blob = Utilities.newBlob(pdfBytes, 'application/pdf', safeName);
  _uploadToGcs(blob, bucket, objectName);

  return { bucket: bucket, objectName: objectName };
}

/**
 * 呼叫 GCF parse_pdf，取得解析結果。
 * @param {string} bucket - GCS bucket 名稱
 * @param {string} objectName - GCS 物件路徑
 * @returns {{ success: boolean, pages: Array, error: string|null, count: number }}
 */
function callGcfParse(bucket, objectName) {
  var gcfUrl = _getProp('GCF_PARSE_PDF_URL') || 'https://asia-east1-obe-project-485614.cloudfunctions.net/parse_pdf';
  var res = _callGcfParsePdf(gcfUrl, bucket, objectName);
  var code = res.code;
  var data = res.data || {};
  var success = code >= 200 && code < 300;
  var count = data.count != null ? data.count : (data.pages && data.pages.length) || 0;
  return {
    success: success,
    pages: data.pages || [],
    error: success ? null : (data.error || 'GCF returned ' + code),
    count: count
  };
}

/**
 * 單一函數：上傳 PDF 並呼叫 GCF 解析（側邊欄可改為分兩步以顯示三階段進度）。
 * @param {string} fileDataBase64 - PDF Base64
 * @param {string} fileName - 檔案名稱
 * @returns {{ success: boolean, pages: Array, error: string|null, count: number }}
 */
function uploadAndProcess(fileDataBase64, fileName) {
  var uploaded = uploadToGcs(fileDataBase64, fileName);
  return callGcfParse(uploaded.bucket, uploaded.objectName);
}

/**
 * GCF 橋接測試：使用 UrlFetchApp 呼叫已部署的 parse_pdf，驗證 GAS 能否連上 GCF。
 * 在 GAS 編輯器選取此函數後執行，從「執行紀錄」查看結果。
 */
function testCloudCall() {
  var url = 'https://asia-east1-obe-project-485614.cloudfunctions.net/parse_pdf';
  var payload = JSON.stringify({
    bucket: 'obe-files',
    blob_path: 'test/connection-check.pdf'
  });
  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: payload,
    muteHttpExceptions: true
  };
  try {
    var response = UrlFetchApp.fetch(url, options);
    var code = response.getResponseCode();
    var body = response.getContentText();
    Logger.log('GCF 回應狀態: ' + code);
    Logger.log('GCF 回應內容: ' + body);
    if (code === 200) {
      Logger.log('[OK] GAS 已成功呼叫 GCF。');
    } else {
      Logger.log('[OK] GAS 已連通 GCF（端點有回應）。');
    }
  } catch (e) {
    Logger.log('[FAIL] GAS 呼叫 GCF 失敗: ' + e.toString());
  }
}
