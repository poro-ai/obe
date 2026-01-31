/**
 * GAS Web App：doGet 入口，供外部以 GET 驗證連結與參數。
 * 部署為「網路應用程式」後，可透過 URL 參數測試。
 */
function doGet(e) {
  var params = e && e.parameter ? e.parameter : {};
  var payload = {
    message: 'Success',
    timestamp: new Date().toISOString(),
    params: params
  };
  var output = ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
  return output;
}
