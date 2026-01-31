/**
 * GAS 測試環境入口（可依需求擴充）
 */
function main() {
  Logger.log('OBE-Project GAS 測試環境已載入');
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
