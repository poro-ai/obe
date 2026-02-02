/**
 * GAS Web App：doGet / doPost 入口。
 * doGet：供外部以 GET 驗證連結與參數。
 * doPost：接收前端 PDF（Base64），上傳至 GCS，呼叫 GCF parse_pdf，回傳解析結果。
 *
 * 版本：每次有更動並部署後請遞增 BACKEND_VERSION，以便前端確認後端是否為最新版。
 * 格式：major.minor.patch，patch 為 2 位數（01–99），例：1.0.06、1.0.07。
 *
 * 需在「專案設定」→「指令碼內容」設定：
 *   GCP_SA_CLIENT_EMAIL  - 服務帳號 email（例：xxx@obe-project-485614.iam.gserviceaccount.com）
 *   GCP_SA_PRIVATE_KEY   - 服務帳號 private_key（PEM，含 -----BEGIN/END-----，換行以 \n 或實際換行）
 *   GCS_BUCKET           - 選填，預設 obe-files
 *   GCF_PARSE_PDF_URL    - 選填，預設 asia-east1 的 parse_pdf URL
 */
/** patch 為 2 位數：01–99，勿用 1.0.6 請用 1.0.06 */
var BACKEND_VERSION = '1.0.09';

/** 供側邊欄／前端顯示系統版本（單一來源，每次更新請遞增 BACKEND_VERSION）。 */
function getVersion() {
  return BACKEND_VERSION;
}

function doGet(e) {
  var params = e && e.parameter ? e.parameter : {};
  if (params.action === 'getParseResult' && params.token) {
    try {
      var data = _getCachedParseResult(params.token);
      var body = data ? data : { error: 'NotFound', message: 'Token expired or invalid' };
      if (params.callback) {
        return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(body) + ')')
          .setMimeType(ContentService.MimeType.JAVASCRIPT);
      }
      return ContentService.createTextOutput(JSON.stringify(body)).setMimeType(ContentService.MimeType.JSON);
    } catch (err) {}
    var errBody = { error: 'NotFound', message: 'Token expired or invalid' };
    if (params.callback) {
      return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(errBody) + ')')
        .setMimeType(ContentService.MimeType.JAVASCRIPT);
    }
    return ContentService.createTextOutput(JSON.stringify(errBody)).setMimeType(ContentService.MimeType.JSON);
  }
  if (params.action === 'getProducts') {
    try {
      var filters = {};
      if (params.category) filters.category = params.category;
      if (params.supplier_name) filters.supplier_name = params.supplier_name;
      if (params.minPrice) filters.minPrice = parseFloat(params.minPrice, 10);
      if (params.maxPrice) filters.maxPrice = parseFloat(params.maxPrice, 10);
      var getProductsOptions = params.env ? { env: params.env } : {};
      var searchResult = searchProducts(filters, getProductsOptions);
      var body = { success: searchResult.success, products: searchResult.products || [], count: searchResult.count || 0, error: searchResult.error || null, version: BACKEND_VERSION };
      if (params.callback) {
        return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(body) + ')')
          .setMimeType(ContentService.MimeType.JAVASCRIPT);
      }
      return ContentService.createTextOutput(JSON.stringify(body)).setMimeType(ContentService.MimeType.JSON);
    } catch (err) {
      var errBody = { success: false, products: [], count: 0, error: err.toString(), version: BACKEND_VERSION };
      if (params.callback) {
        return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(errBody) + ')')
          .setMimeType(ContentService.MimeType.JAVASCRIPT);
      }
      return ContentService.createTextOutput(JSON.stringify(errBody)).setMimeType(ContentService.MimeType.JSON);
    }
  }
  if (params.action === 'getProductMasterSheetUrl') {
    try {
      var urlOptions = params.env ? { env: params.env } : {};
      var urlResult = getProductMasterSheetUrl(urlOptions);
      var urlBody = { success: urlResult.success, sheetUrl: urlResult.sheetUrl || null, error: urlResult.error || null, version: BACKEND_VERSION };
      if (params.callback) {
        return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(urlBody) + ')')
          .setMimeType(ContentService.MimeType.JAVASCRIPT);
      }
      return ContentService.createTextOutput(JSON.stringify(urlBody)).setMimeType(ContentService.MimeType.JSON);
    } catch (err) {
      var urlErrBody = { success: false, sheetUrl: null, error: err.toString(), version: BACKEND_VERSION };
      if (params.callback) {
        return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(urlErrBody) + ')')
          .setMimeType(ContentService.MimeType.JAVASCRIPT);
      }
      return ContentService.createTextOutput(JSON.stringify(urlErrBody)).setMimeType(ContentService.MimeType.JSON);
    }
  }
  var payload = {
    message: 'Success',
    timestamp: new Date().toISOString(),
    params: params,
    version: BACKEND_VERSION
  };
  if (params.callback) {
    return ContentService.createTextOutput(params.callback + '(' + JSON.stringify(payload) + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

/** CacheService 單 key 約 100KB，分塊儲存解析結果，供側邊欄→編輯器帶入。 */
var _parseResultChunkSize = 90 * 1024;

function _storeParseResultChunked(pagesData) {
  if (!pagesData || !Array.isArray(pagesData) || pagesData.length === 0) return null;
  var json = JSON.stringify(pagesData);
  var token = Utilities.getUuid().slice(0, 12).replace(/-/g, '');
  var cache = CacheService.getScriptCache();
  var i = 0;
  var start = 0;
  while (start < json.length) {
    var chunk = json.slice(start, start + _parseResultChunkSize);
    cache.put('obe_parse_' + token + '_' + i, chunk, 600);
    start += _parseResultChunkSize;
    i++;
  }
  cache.put('obe_parse_' + token + '_meta', String(i), 600);
  return token;
}

function _getCachedParseResult(token) {
  if (!token) return null;
  var cache = CacheService.getScriptCache();
  var meta = cache.get('obe_parse_' + token + '_meta');
  if (!meta) return null;
  var count = parseInt(meta, 10);
  if (isNaN(count) || count <= 0) return null;
  var parts = [];
  for (var i = 0; i < count; i++) {
    var part = cache.get('obe_parse_' + token + '_' + i);
    if (part == null) return null;
    parts.push(part);
  }
  return JSON.parse(parts.join(''));
}

/**
 * 接收前端 POST（Content-Type: text/plain）。
 * action=saveToSheets：將 body.pages（編輯器匯出）寫入 Google Sheets，回傳 { success, sheetUrl }。
 * 無 action 或 pdfBase64：原有流程（上傳 PDF → GCF 解析 → 回傳 pages）。
 */
function doPost(e) {
  var result = { success: false, statusCode: 500, error: null, count: null, pages: null, version: BACKEND_VERSION };
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

    if (body.action === 'saveToSheets') {
      return _jsonOutput(_saveToSheets(body));
    }
    if (body.action === 'insertToSlides') {
      return _jsonOutput(_insertToSlides(body));
    }
    if (body.action === 'importToProductMaster') {
      return _jsonOutput(_importToProductMaster(body));
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

    var pdfBytes = Utilities.base64Decode(pdfBase64);
    var pdfBlob = Utilities.newBlob(pdfBytes, 'application/pdf', fileName);
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
 * 將編輯器匯出的 pages 寫入 Google Sheets。
 * body.pages: [{ page, elements: [{ type, content, description }] }]
 * 若未設定 SPREADSHEET_ID 則建立新試算表並寫入。
 */
function _saveToSheets(body) {
  var out = { success: false, statusCode: 500, error: null, sheetUrl: null, version: BACKEND_VERSION };
  try {
    var pages = body.pages;
    if (!pages || !Array.isArray(pages)) {
      out.error = 'Missing or invalid pages array';
      out.statusCode = 400;
      return out;
    }
    var spreadsheet;
    var sheetId = _getProp('SPREADSHEET_ID');
    if (sheetId) {
      try {
        spreadsheet = SpreadsheetApp.openById(sheetId);
      } catch (err) {
        spreadsheet = null;
      }
    }
    if (!spreadsheet) {
      spreadsheet = SpreadsheetApp.create('OBE Editor Export ' + new Date().toISOString().slice(0, 10));
      PropertiesService.getScriptProperties().setProperty('SPREADSHEET_ID', spreadsheet.getId());
    }
    var sheet = spreadsheet.getSheets()[0];
    sheet.setName('Export');
    sheet.clear();
    sheet.getRange(1, 1, 1, 4).setValues([['Page', 'Type', 'Content', 'Description']]);
    sheet.getRange(1, 1, 1, 4).setFontWeight('bold');
    var row = 2;
    for (var p = 0; p < pages.length; p++) {
      var pageNum = pages[p].page != null ? pages[p].page : (p + 1);
      var elements = pages[p].elements || [];
      for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        var content = (el.content || '').toString();
        if (content.length > 50000) content = content.slice(0, 50000) + '…';
        sheet.getRange(row, 1, row, 4).setValues([[pageNum, el.type || 'text', content, (el.description || '').toString()]]);
        row++;
      }
    }
    out.success = true;
    out.statusCode = 200;
    out.sheetUrl = spreadsheet.getUrl();
    return out;
  } catch (err) {
    out.error = err.toString();
    out.statusCode = 500;
    return out;
  }
}

/**
 * 將 elements 插入指定投影片（與 Main.js insertElementsToSlide 相同排版邏輯）。
 * 供 insertToSlides（瀏覽器編輯器）與附加元件共用。
 */
function _insertElementsIntoSlide(slide, elements) {
  if (!elements || elements.length === 0) return;
  var pageWidth = 720;
  var marginLeft = 20;
  var imageWidth = Math.round(pageWidth * 0.3);
  var imageHeight = 162;
  var textLeft = marginLeft + imageWidth + 10;
  var textWidth = pageWidth - textLeft - marginLeft;
  var textHeight = 80;
  var rowOffset = 50;
  var offsetY = 20;

  for (var i = 0; i < elements.length; i++) {
    var el = elements[i];
    var type = (el.type || 'text').toLowerCase();
    var content = (el.content || '').toString();
    var desc = (el.description || el.summary || '').toString();

    if (type === 'image') {
      try {
        var imageSource = null;
        if (content.indexOf('data:') === 0) {
          var comma = content.indexOf(',');
          if (comma >= 0) {
            var b64 = content.substring(comma + 1);
            var mime = 'image/png';
            if (content.indexOf('image/jpeg') >= 0 || content.indexOf('image/jpg') >= 0) mime = 'image/jpeg';
            imageSource = Utilities.newBlob(Utilities.base64Decode(b64), mime, 'img');
          }
        } else if (content.indexOf('http') === 0) {
          imageSource = content;
        }
        if (imageSource) {
          slide.insertImage(imageSource, marginLeft, offsetY, imageWidth, imageHeight);
        }
      } catch (imgErr) {}
      var textToShow = desc || '(圖片)';
      var tb = slide.insertTextBox(textToShow, textLeft, offsetY, textWidth, textHeight);
      try {
        var tr = tb.getText();
        if (tr && tr.getTextStyle) {
          tr.getTextStyle().setFontFamily('Microsoft JhengHei');
          tr.getTextStyle().setFontSize(14);
        }
      } catch (e) {}
      offsetY += rowOffset;
    } else {
      var txt = content || desc || '';
      if (txt.length > 500) txt = txt.substring(0, 500) + '…';
      var box = slide.insertTextBox(txt, marginLeft, offsetY, pageWidth - marginLeft * 2, textHeight);
      try {
        var textRange = box.getText();
        if (textRange && textRange.getTextStyle) {
          textRange.getTextStyle().setFontFamily('Microsoft JhengHei');
          textRange.getTextStyle().setFontSize(14);
        }
      } catch (e) {}
      offsetY += rowOffset;
    }
  }
}

/**
 * 瀏覽器編輯器「插入至 Google 簡報」：依 presentationId 開啟簡報並將 elements 插入指定投影片。
 * body: { action: 'insertToSlides', presentationId: string, elements: Array, slideIndex?: number }
 * 部署 Web App 時請設為「以造訪使用者的身分執行」，否則無法寫入使用者的簡報。
 */
function _insertToSlides(body) {
  var out = { success: false, statusCode: 500, error: null, slideIndex: null, version: BACKEND_VERSION };
  try {
    var presentationId = body.presentationId;
    var elements = body.elements;
    if (!presentationId || !elements || !Array.isArray(elements)) {
      out.error = 'Missing presentationId or elements array';
      out.statusCode = 400;
      return out;
    }
    var presentation = SlidesApp.openById(presentationId);
    var slides = presentation.getSlides();
    if (slides.length === 0) {
      out.error = 'Presentation has no slides';
      out.statusCode = 400;
      return out;
    }
    var slideIndex = Math.min(parseInt(body.slideIndex, 10) || 0, slides.length - 1);
    if (slideIndex < 0) slideIndex = 0;
    var slide = slides[slideIndex];
    _insertElementsIntoSlide(slide, elements);
    out.success = true;
    out.statusCode = 200;
    out.slideIndex = slideIndex;
    return out;
  } catch (err) {
    out.error = err.toString();
    out.statusCode = 500;
    return out;
  }
}

/**
 * 將編輯器/解析結果 pages 匯入商品主檔。
 * body: { action: 'importToProductMaster', pages: Array, rawText?: string, env?: 'prod'|'test' }
 * - 若有 rawText 則上傳為原文 .txt 並填寫每筆商品的 raw_text_url；否則由 pages 組出全文上傳。
 * - 每頁轉為一筆商品；圖片上傳 GCS 後 URL 填入 images。
 */
function _importToProductMaster(body) {
  var out = { success: false, statusCode: 500, error: null, count: 0, raw_text_url: null, productIds: [], version: BACKEND_VERSION };
  try {
    var pages = body.pages;
    if (!pages || !Array.isArray(pages) || pages.length === 0) {
      out.error = 'Missing or invalid pages array';
      out.statusCode = 400;
      return out;
    }
    var bucket = _getProp('GCS_BUCKET') || 'obe-files';
    var docId = 'doc-' + new Date().getTime() + '-' + Utilities.getUuid().slice(0, 8);
    var rawTextContent = (body.rawText && body.rawText.toString()) || '';
    if (!rawTextContent) {
      var parts = [];
      for (var p = 0; p < pages.length; p++) {
        parts.push('--- 第 ' + (pages[p].page != null ? pages[p].page : (p + 1)) + ' 頁 ---');
        var elements = pages[p].elements || [];
        for (var i = 0; i < elements.length; i++) {
          var el = elements[i];
          var type = (el.type || '').toString().toLowerCase();
          if (type === 'text' && (el.content || '').toString()) {
            parts.push((el.content || '').toString());
          }
          if ((el.description || '').toString()) parts.push((el.description || '').toString());
        }
        parts.push('');
      }
      rawTextContent = parts.join('\n');
    }
    var rawTextUrl = null;
    if (rawTextContent.length > 0) {
      try {
        rawTextUrl = _uploadRawTextToGcs(rawTextContent, bucket, 'raw-text/' + docId + '/full_text.txt');
      } catch (uploadErr) {
        out.error = 'Failed to upload raw text: ' + uploadErr.toString();
        out.statusCode = 500;
        return out;
      }
    }
    out.raw_text_url = rawTextUrl;

    var products = [];
    for (var pi = 0; pi < pages.length; pi++) {
      var pageNum = pages[pi].page != null ? pages[pi].page : (pi + 1);
      var productId = 'PROD-' + Utilities.getUuid().slice(0, 8).toUpperCase();
      var productName = '';
      var notesParts = [];
      var imageUrls = [];
      var elements = pages[pi].elements || [];
      var imgIndex = 0;
      for (var ei = 0; ei < elements.length; ei++) {
        var elem = elements[ei];
        var elemType = (elem.type || '').toString().toLowerCase();
        var content = (elem.content || '').toString();
        var desc = (elem.description || '').toString();
        if (elemType === 'text') {
          if (content && !productName) productName = content.length > 200 ? content.slice(0, 200) + '…' : content;
          if (content) notesParts.push(content);
          if (desc) notesParts.push(desc);
        } else if (elemType === 'image' && content) {
          var b64 = content;
          var mime = 'image/png';
          if (content.indexOf('base64,') >= 0) {
            var comma = content.indexOf(',');
            if (comma >= 0) {
              b64 = content.substring(comma + 1);
              if (content.indexOf('image/jpeg') >= 0 || content.indexOf('image/jpg') >= 0) mime = 'image/jpeg';
            }
          }
          if (b64.length > 0) {
            try {
              var imgPath = 'product-images/' + productId + '/image_' + (imgIndex++) + (mime === 'image/jpeg' ? '.jpg' : '.png');
              var imgUrl = _uploadImageToGcs(b64, bucket, imgPath, mime);
              imageUrls.push(imgUrl);
            } catch (imgErr) {}
          }
          if (desc) notesParts.push(desc);
        }
      }
      if (!productName) productName = '第 ' + pageNum + ' 頁';
      products.push({
        product_id: productId,
        product_name: productName,
        raw_text_url: rawTextUrl || '',
        images: imageUrls.join(','),
        notes: notesParts.join('\n').slice(0, 5000)
      });
    }

    var options = body.env ? { env: body.env } : {};
    var importResult = importProducts(products, options);
    out.success = importResult.success;
    out.count = importResult.count || 0;
    out.statusCode = out.success ? 200 : (importResult.errors && importResult.errors.length > 0 ? 207 : 500);
    if (importResult.errors && importResult.errors.length > 0) out.error = importResult.error;
    if (importResult.count > 0) {
      for (var k = 0; k < products.length; k++) {
        if (products[k].product_id) out.productIds.push(products[k].product_id);
      }
    }
    return out;
  } catch (err) {
    out.error = err.toString();
    out.statusCode = 500;
    return out;
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
 * 使用 base64Encode(str, Charset.UTF_8) 字串簽章，避免位元組陣列簽章 (number[], Charset) 不符。
 */
function _base64UrlEncode(str) {
  var raw = Utilities.base64Encode(str, Utilities.Charset.UTF_8);
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
 * @param {Blob} blob
 * @param {string} bucket
 * @param {string} objectName
 * @param {string} contentType 選填，預設 application/pdf
 */
function _uploadToGcs(blob, bucket, objectName, contentType) {
  contentType = contentType || 'application/pdf';
  var token = _getGcpAccessToken();
  var url = 'https://storage.googleapis.com/upload/storage/v1/b/' + encodeURIComponent(bucket) + '/o?uploadType=media&name=' + encodeURIComponent(objectName);
  var options = {
    method: 'post',
    contentType: contentType,
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
 * 上傳純文字至 GCS 作為 .txt 檔（供原文比對校正用）。
 * @param {string} textContent 整份文件原始文字（UTF-8）
 * @param {string} bucket 預設從 GCS_BUCKET 讀取
 * @param {string} objectPath 例：raw-text/doc-001/full_text.txt
 * @return {string} gs://bucket/objectPath
 */
function _uploadRawTextToGcs(textContent, bucket, objectPath) {
  bucket = bucket || _getProp('GCS_BUCKET') || 'obe-files';
  var blob = Utilities.newBlob(textContent || '', 'text/plain; charset=utf-8', 'full_text.txt');
  _uploadToGcs(blob, bucket, objectPath, 'text/plain; charset=utf-8');
  return 'gs://' + bucket + '/' + objectPath;
}

/**
 * 上傳 Base64 圖片至 GCS（供商品主檔 images URL）。
 * @param {string} base64Content 不含 data URI 前綴的 base64 字串
 * @param {string} bucket 預設從 GCS_BUCKET 讀取
 * @param {string} objectPath 例：product-images/PROD-xxx/image_1.png
 * @param {string} mimeType 例：image/png, image/jpeg
 * @return {string} gs://bucket/objectPath
 */
function _uploadImageToGcs(base64Content, bucket, objectPath, mimeType) {
  bucket = bucket || _getProp('GCS_BUCKET') || 'obe-files';
  mimeType = mimeType || 'image/png';
  var bytes = Utilities.base64Decode(base64Content);
  var blob = Utilities.newBlob(bytes, mimeType, objectPath.split('/').pop() || 'image');
  _uploadToGcs(blob, bucket, objectPath, mimeType);
  return 'gs://' + bucket + '/' + objectPath;
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
