/**
 * Google Slides 附加元件／容器腳本入口。
 *
 * 側邊欄入口：
 * - onOpen(e)：新增選單按鈕（擴充功能 → OBE → 開啟 AI 解析側邊欄），使用 createAddonMenu()，fallback 為 createMenu('OBE')。
 * - showSidebar()：呼叫 HtmlService.createHtmlOutputFromFile('sidebar') 載入 gas/sidebar.html，檔名須一致（sidebar.html → 'sidebar'）。
 *
 * GAS 中轉（檔案流 → GCS → GCF）：
 * - uploadAndProcess(fileDataBase64, fileName)：單一入口，將 PDF Base64 上傳至 GCS 後觸發 GCF parse_pdf，回傳 { success, pages, error, count }。
 * - 側邊欄為顯示三階段進度（讀取檔案 / 上傳雲端 / AI 解析），可改為分步呼叫 uploadToGcs 與 callGcfParse。
 *
 * 其他：uploadToGcs、callGcfParse、insertElementsToSlide；依賴 web_app.js 的 _getProp、_uploadToGcs、_callGcfParsePdf。
 */

function onOpen(e) {
  var ui = SlidesApp.getUi();
  // 附加元件選單（正式安裝時會出現在「擴充功能」底下）
  try {
    ui.createAddonMenu()
      .addItem('開啟 AI 解析側邊欄', 'showSidebar')
      .addToUi();
  } catch (err) {}
  // 頂層選單「OBE」：測試安裝時「擴充功能」底下常無項目，改從這裡開側邊欄
  ui.createMenu('OBE')
    .addItem('開啟 AI 解析側邊欄', 'showSidebar')
    .addToUi();
}

/**
 * 安裝後觸發，呼叫 onOpen 以立即顯示選單。
 */
function onInstall(e) {
  onOpen(e);
}

/**
 * Slides 附加元件首頁觸發（addOns.slides.homepageTrigger.runFunction）。
 * 必須存在並回傳 Card 陣列，否則會報「找不到指令碼函式：onSlidesHomepage」。
 * 測試安裝時選單常不顯示，改在卡片上放按鈕直接開啟 AI 解析側邊欄。
 */
function onSlidesHomepage(e) {
  var openAction = CardService.newAction().setFunctionName('showSidebar');
  var version = (typeof getVersion === 'function' ? getVersion() : null) || '—';
  var card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle('OBE'))
    .addSection(CardService.newCardSection()
      .addWidget(CardService.newTextParagraph().setText('上傳 PDF 後由 AI 解析圖文，再插入投影片。'))
      .addWidget(CardService.newTextParagraph().setText('版本：v' + version))
      .addWidget(CardService.newTextButton()
        .setText('開啟 AI 解析側邊欄')
        .setOnClickAction(openAction)))
    .build();
  return [card];
}

/**
 * 通用附加元件首頁觸發（addOns.common.homepageTrigger.runFunction）。
 */
function onHomepage(e) {
  return onSlidesHomepage(e);
}

/**
 * 取得「瀏覽器編輯器」網址（含目前簡報 ID 與 GAS Web App URL），供側邊欄按鈕開啟新分頁。
 * 需在指令碼內容設定 EDITOR_BASE_URL（例：https://poro-ai.github.io/obe/）、GAS_WEB_APP_URL（選填，會帶入編輯器）。
 */
function getEditorUrlWithPresentationId() {
  var presentation = SlidesApp.getActivePresentation();
  var id = presentation.getId();
  var base = _getProp('EDITOR_BASE_URL') || 'https://poro-ai.github.io/obe/';
  base = base.replace(/\/$/, '');
  var gasUrl = _getProp('GAS_WEB_APP_URL') || '';
  var url = base + '/editor.html?presentationId=' + encodeURIComponent(id);
  if (gasUrl) url += '&gasUrl=' + encodeURIComponent(gasUrl);
  return { url: url };
}

/**
 * 取得帶 token 的編輯器網址（token 由側邊欄在解析完成時從 callGcfParse 取得並保存）。
 * 供「在瀏覽器開啟編輯器」按鈕使用：傳入 savedEditorToken，若有則附加至 URL。
 */
function getEditorUrlWithToken(editorToken) {
  var obj = getEditorUrlWithPresentationId();
  var url = obj.url;
  if (editorToken) {
    url += (url.indexOf('?') >= 0 ? '&' : '?') + 'token=' + encodeURIComponent(editorToken);
  }
  return { url: url };
}

/**
 * 開啟 AI 解析側邊欄。引用的檔名須與左側檔案面板中的 HTML 檔名一致（不含副檔名）：
 * 檔案為 sidebar.html → createHtmlOutputFromFile('sidebar')。
 * 使用 NATIVE sandbox 以允許解析結果中的 data URI 圖片顯示（IFRAME 預設會擋 data:）。
 * 瀏覽器可能顯示「iframe allow-scripts + allow-same-origin 可逃脫 sandbox」警告，為 NATIVE 模式取捨，可忽略。
 */
function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('sidebar')
    .setTitle('AI 解析')
    .setWidth(320)
    .setSandboxMode(HtmlService.SandboxMode.NATIVE);
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
 * 呼叫 GCF parse_pdf，取得解析結果。成功時在伺服器暫存 pages 並回傳 editorToken，供「在瀏覽器開啟編輯器」帶入資料。
 * @param {string} bucket - GCS bucket 名稱
 * @param {string} objectName - GCS 物件路徑
 * @returns {{ success: boolean, pages: Array, error: string|null, count: number, editorToken: string|null }}
 */
function callGcfParse(bucket, objectName) {
  var gcfUrl = _getProp('GCF_PARSE_PDF_URL') || 'https://asia-east1-obe-project-485614.cloudfunctions.net/parse_pdf';
  var res = _callGcfParsePdf(gcfUrl, bucket, objectName);
  var code = res.code;
  var data = res.data || {};
  var success = code >= 200 && code < 300;
  var count = data.count != null ? data.count : (data.pages && data.pages.length) || 0;
  var pages = data.pages || [];
  var editorToken = null;
  if (success && pages.length > 0) {
    try {
      editorToken = _storeParseResultChunked(pages);
    } catch (e) {}
  }
  return {
    success: success,
    pages: pages,
    error: success ? null : (data.error || 'GCF returned ' + code),
    count: count,
    editorToken: editorToken
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
 * 將側邊欄選取的解析元素插入目前投影片。
 * @param {Array<{type: string, content: string, description: string}>} elements - 選取的元素列表
 * 圖片：置於左側，寬度為投影片 30%；文字：置於圖片右側，微軟正黑體 14pt；連續插入時向下位移 50pt。
 */
function insertElementsToSlide(elements) {
  if (!elements || elements.length === 0) {
    return;
  }
  var presentation = SlidesApp.getActivePresentation();
  var selection = presentation.getSelection();
  var currentPage = selection.getCurrentPage();
  if (!currentPage) {
    var slides = presentation.getSlides();
    currentPage = slides.length > 0 ? slides[0] : null;
  }
  if (!currentPage) {
    throw new Error('無法取得目前投影片');
  }
  var slide = currentPage.asSlide();
  var pageWidth = 720;
  var pageHeight = 405;
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
        var blob = null;
        var imageSource = null;
        if (content.indexOf('data:') === 0) {
          var comma = content.indexOf(',');
          if (comma >= 0) {
            var b64 = content.substring(comma + 1);
            var mime = 'image/png';
            if (content.indexOf('image/jpeg') >= 0 || content.indexOf('image/jpg') >= 0) mime = 'image/jpeg';
            blob = Utilities.newBlob(Utilities.base64Decode(b64), mime, 'img');
            imageSource = blob;
          }
        } else if (content.indexOf('http') === 0) {
          imageSource = content;
        }
        if (imageSource) {
          slide.insertImage(imageSource, marginLeft, offsetY, imageWidth, imageHeight);
        }
      } catch (imgErr) {
        Logger.log('insertElementsToSlide image skip: ' + imgErr.toString());
      }
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
