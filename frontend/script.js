/**
 * 前端與 GAS doPost 通訊：以 Base64 上傳 PDF，顯示進度條，並顯示 GAS 回傳的 GCF 解析結果。
 * 使用 Content-Type: text/plain;charset=utf-8 以避開 CORS 預檢（OPTIONS），body 仍為 JSON 字串。
 */

(function () {
  var gasUrlEl = document.getElementById('gasUrl');
  var fileEl = document.getElementById('file');
  var fileNameEl = document.getElementById('fileName');
  var uploadBtn = document.getElementById('upload');
  var progressWrap = document.getElementById('progressWrap');
  var progressBar = document.getElementById('progressBar');
  var progressText = document.getElementById('progressText');
  var resultEl = document.getElementById('result');

  function showResult(text, isError) {
    resultEl.textContent = text;
    resultEl.className = isError ? 'error' : '';
  }

  function setProgress(percent, text) {
    progressWrap.style.display = 'block';
    progressBar.style.width = (percent || 0) + '%';
    progressText.textContent = text || '';
  }

  function hideProgress() {
    progressWrap.style.display = 'none';
    progressText.textContent = '';
  }

  fileEl.addEventListener('change', function () {
    var f = fileEl.files[0];
    fileNameEl.textContent = f ? f.name + ' (' + (f.size / 1024).toFixed(1) + ' KB)' : '';
  });

  uploadBtn.addEventListener('click', function () {
    var gasUrl = (gasUrlEl.value || '').trim();
    var file = fileEl.files[0];

    if (!gasUrl) {
      showResult('請輸入 GAS Web App 網址（doPost 入口）', true);
      return;
    }
    if (!file) {
      showResult('請選擇一個 PDF 檔案', true);
      return;
    }
    if (file.type !== 'application/pdf') {
      showResult('請選擇 PDF 檔案', true);
      return;
    }

    uploadBtn.disabled = true;
    showResult('讀取檔案中…');
    setProgress(5, '讀取中…');

    var reader = new FileReader();
    reader.onload = function () {
      var base64 = reader.result.split(',')[1];
      if (!base64) {
        showResult('無法取得檔案 Base64', true);
        uploadBtn.disabled = false;
        hideProgress();
        return;
      }
      setProgress(10, '上傳至 GAS…');

      var xhr = new XMLHttpRequest();
      var data = { pdfBase64: base64, fileName: file.name };
      var body = JSON.stringify(data);

      xhr.upload.addEventListener('progress', function (e) {
        if (e.lengthComputable) {
          var pct = 10 + Math.round((e.loaded / e.total) * 50);
          setProgress(pct, '上傳中 ' + pct + '%');
        }
      });

      xhr.addEventListener('load', function () {
        setProgress(95, 'GAS 處理中…');
        var status = xhr.status;
        var responseText = xhr.responseText || '';

        console.log('[GAS 回傳] status:', status, 'response:', responseText.substring(0, 500) + (responseText.length > 500 ? '…' : ''));

        try {
          var resData = JSON.parse(responseText);
          if (status >= 200 && status < 300) {
            setProgress(100, '完成');
            var count = resData.count != null ? resData.count : (resData.pages && resData.pages.length);
            console.log('[GAS 回傳] 解析成功，筆數:', count, 'data:', resData);
            showResult(
              '成功。共 ' + (count || 0) + ' 筆頁面。\n\n' +
              JSON.stringify(resData, null, 2)
            );
          } else {
            console.warn('[GAS 回傳] 錯誤:', status, resData);
            showResult('錯誤 ' + status + ': ' + (resData.error || resData.message || responseText), true);
          }
        } catch (err) {
          console.error('[GAS 回傳] 解析失敗:', err, 'raw:', responseText.substring(0, 300));
          showResult('回應解析失敗: ' + responseText.substring(0, 200), true);
        }
        uploadBtn.disabled = false;
        hideProgress();
      });

      xhr.addEventListener('error', function (e) {
        console.error('[GAS 請求] 網路或 CORS 錯誤:', e);
        showResult('上傳請求失敗（網路或 CORS）', true);
        uploadBtn.disabled = false;
        hideProgress();
      });

      xhr.addEventListener('abort', function () {
        console.warn('[GAS 請求] 已中止');
        uploadBtn.disabled = false;
        hideProgress();
      });

      xhr.open('POST', gasUrl);
      xhr.setRequestHeader('Content-Type', 'text/plain;charset=utf-8');
      xhr.send(body);
    };

    reader.onerror = function () {
      showResult('讀取檔案失敗', true);
      uploadBtn.disabled = false;
      hideProgress();
    };
    reader.readAsDataURL(file);
  });
})();
