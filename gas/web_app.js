/**
 * GAS Web App：doGet / doPost 入口。
 * doGet：供外部以 GET 驗證連結與參數。
 * doPost：接收前端 PDF（Base64），上傳至 GCS，呼叫 GCF parse_pdf，回傳解析結果。
 *
 * 需在「專案設定」→「指令碼內容」設定：
 *   GCP_SA_CLIENT_EMAIL  - 服務帳號 email（例：xxx@obe-project-485614.iam.gserviceaccount.com）
 *   GCP_SA_PRIVATE_KEY   - 服務帳號 private_key（PEM，含 -----BEGIN/END-----，換行以 \n 或實際換行）
 *   GCS_BUCKET           - 選填，預設 obe-files
 *   GCF_PARSE_PDF_URL    - 選填，預設 asia-east1 的 parse_pdf URL
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

/**
 * 接收前端 POST（Content-Type: text/plain）。
 * 從 e.postData.contents 讀取原始字串，使用 JSON.parse 解析。
 * 處理邏輯後以 ContentService.createTextOutput 回傳 JSON 字串，並 setMimeType(ContentService.MimeType.JSON)。
 * 外層 try-catch 確保發生錯誤時也回傳 JSON 格式的錯誤訊息。
 */
function doPost(e) {
  var result = { success: false, statusCode: 500, error: null, count: null, pages: null };
  try {
    if (!e || !e.postData || !e.postData.contents) {
      result.error = 'Missing POST body';
      result.statusCode = 400;
      return _jsonOutput(result);
    }
    var rawString = e.postData.contents;
    var body;
    try {
      body = JSON.parse(rawString);
    } catch (parseErr) {
      result.error = 'Invalid JSON in body: ' + parseErr.toString();
      result.statusCode = 400;
      return _jsonOutput(result);
    }
    var pdfBase64 = body.pdfBase64;
    var fileName = (body.fileName || 'upload.pdf').replace(/[^a-zA-Z0-9._-]/g, '_');
    if (!pdfBase64) {
      result.error = 'Missing pdfBase64';
      result.statusCode = 400;
      return _jsonOutput(result);
    }

    var bucket = _getProp('GCS_BUCKET') || 'obe-files';
    var prefix = 'uploads/' + new Date().getTime() + '_';
    var objectName = prefix + fileName;

    var pdfBlob = Utilities.newBlob(Utilities.base64Decode(pdfBase64), 'application/pdf', fileName);
    _uploadToGcs(pdfBlob, bucket, objectName);

    var gcfUrl = _getProp('GCF_PARSE_PDF_URL') || 'https://asia-east1-obe-project-485614.cloudfunctions.net/parse_pdf';
    var gcfResponse = _callGcfParsePdf(gcfUrl, bucket, objectName);

    var code = gcfResponse.code;
    var data = gcfResponse.data;
    if (code >= 200 && code < 300 && data) {
      result.success = true;
      result.statusCode = 200;
      result.count = data.count != null ? data.count : (data.pages && data.pages.length);
      result.pages = data.pages || [];
      return _jsonOutput(result);
    }
    result.error = (data && data.error) ? data.error : ('GCF returned ' + code);
    result.statusCode = code >= 400 ? code : 500;
    return _jsonOutput(result);
  } catch (err) {
    result.error = err.toString();
    result.statusCode = 500;
    return _jsonOutput(result);
  }
}

/**
 * 使用 ContentService.createTextOutput 回傳 JSON 字串，務必 setMimeType(ContentService.MimeType.JSON)。
 */
function _jsonOutput(obj) {
  var output = ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
  return output;
}

function _getProp(key) {
  try {
    return PropertiesService.getScriptProperties().getProperty(key) || null;
  } catch (e) {
    return null;
  }
}

/**
 * Base64url 編碼（無 padding，+ -> -, / -> _）。
 * 第一個參數為位元組陣列時，base64Encode 僅接受一個參數，不可傳 Charset。
 * 此結果用於 JWT 的 assertion（POST body），非 URL 路徑，故以 replace 轉成 base64url 即可，無須 base64EncodeWebSafe。
 */
function _base64UrlEncode(str) {
  var bytes = Utilities.newBlob(str).getBytes();
  var raw = Utilities.base64Encode(bytes);
  return raw.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * 使用服務帳號取得 GCP Access Token（JWT 流程）。
 * 需設定 GCP_SA_CLIENT_EMAIL、GCP_SA_PRIVATE_KEY。
 */
function _getGcpAccessToken() {
  var email = _getProp('GCP_SA_CLIENT_EMAIL');
  var keyPem = _getProp('GCP_SA_PRIVATE_KEY');
  if (!email || !keyPem) {
    throw new Error('Missing GCP_SA_CLIENT_EMAIL or GCP_SA_PRIVATE_KEY in Script Properties');
  }
  keyPem = keyPem.replace(/\\n/g, '\n');
  var now = Math.floor(Date.now() / 1000);
  var header = { alg: 'RS256', typ: 'JWT' };
  var payload = {
    iss: email,
    sub: email,
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: now + 3600,
    scope: 'https://www.googleapis.com/auth/cloud-platform'
  };
  var headerB64 = _base64UrlEncode(JSON.stringify(header));
  var payloadB64 = _base64UrlEncode(JSON.stringify(payload));
  var toSign = headerB64 + '.' + payloadB64;
  var sigBytes = Utilities.computeRsaSha256Signature(toSign, keyPem);
  var sigB64 = Utilities.base64EncodeWebSafe(sigBytes).replace(/=+$/, '');
  var jwt = toSign + '.' + sigB64;

  var tokenUrl = 'https://oauth2.googleapis.com/token';
  var options = {
    method: 'post',
    contentType: 'application/x-www-form-urlencoded',
    payload: 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=' + jwt,
    muteHttpExceptions: true
  };
  var res = UrlFetchApp.fetch(tokenUrl, options);
  var code = res.getResponseCode();
  var json = JSON.parse(res.getContentText());
  if (code !== 200 || !json.access_token) {
    throw new Error('Failed to get access token: ' + (json.error || code));
  }
  return json.access_token;
}

/**
 * 上傳 Blob 至 GCS（使用 GCS JSON API uploadType=media）。
 */
function _uploadToGcs(blob, bucket, objectName) {
  var token = _getGcpAccessToken();
  var url = 'https://storage.googleapis.com/upload/storage/v1/b/' + encodeURIComponent(bucket) + '/o?uploadType=media&name=' + encodeURIComponent(objectName);
  var options = {
    method: 'post',
    contentType: 'application/pdf',
    payload: blob,
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  };
  var res = UrlFetchApp.fetch(url, options);
  var code = res.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error('GCS upload failed: ' + code + ' ' + res.getContentText());
  }
}

/**
 * 呼叫 GCF parse_pdf，傳入 bucket 與 blob_path。
 */
function _callGcfParsePdf(gcfUrl, bucket, blobPath) {
  var payload = JSON.stringify({ bucket: bucket, blob_path: blobPath });
  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: payload,
    muteHttpExceptions: true
  };
  var res = UrlFetchApp.fetch(gcfUrl, options);
  var code = res.getResponseCode();
  var data = {};
  try {
    data = JSON.parse(res.getContentText());
  } catch (e) {}
  return { code: code, data: data };
}
