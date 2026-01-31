/**
 * 前端與 GAS doPost 通訊：以 Base64 上傳 PDF，顯示進度條，並顯示 GAS 回傳的 GCF 解析結果。
 * 使用 fetch，Content-Type: text/plain;charset=utf-8 以避開 CORS 預檢（OPTIONS），mode: 'cors'，body 為 JSON.stringify。
 * 版本：每次有更動請遞增 index.html 的 meta name="version" content，與後端版本比對以確認是否為最新。
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
  var frontendVersionEl = document.getElementById('frontendVersion');
  var backendVersionEl = document.getElementById('backendVersion');

  var metaVersion = document.querySelector('meta[name="version"]');
  var FRONTEND_VERSION = (metaVersion && metaVersion.getAttribute('content')) || '—';
  frontendVersionEl.textContent = FRONTEND_VERSION;

  function setBackendVersion(version) {
    if (backendVersionEl) backendVersionEl.textContent = version || '—';
  }

  function fetchBackendVersion() {
    var gasUrl = (gasUrlEl.value || '').trim();
    if (!gasUrl) {
      setBackendVersion('未設定網址');
      return;
    }
    fetch(gasUrl, { method: 'GET', mode: 'cors' })
      .then(function (res) { return res.text(); })
      .then(function (text) {
        try {
          var data = JSON.parse(text);
          setBackendVersion(data.version || '—');
        } catch (e) {
          setBackendVersion('取得失敗');
        }
      })
      .catch(function () {
        setBackendVersion('連線失敗');
      });
  }

  fetchBackendVersion();

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

      var data = { pdfBase64: base64, fileName: file.name };
      var body = JSON.stringify(data);

      fetch(gasUrl, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'text/plain;charset=utf-8'
        },
        body: body
      })
        .then(function (res) {
          setProgress(95, 'GAS 處理中…');
          var status = res.status;
          return res.text().then(function (responseText) {
            return { status: status, responseText: responseText };
          });
        })
        .then(function (out) {
          var status = out.status;
          var responseText = out.responseText || '';

          console.log('[GAS 回傳] status:', status, 'response:', responseText.substring(0, 500) + (responseText.length > 500 ? '…' : ''));

          try {
            var resData = JSON.parse(responseText);
            if (resData.version) setBackendVersion(resData.version);
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
        })
        .catch(function (err) {
          console.error('[GAS 請求] 網路或 CORS 錯誤:', err);
          showResult('上傳請求失敗（網路或 CORS）', true);
          uploadBtn.disabled = false;
          hideProgress();
        });
    };

    reader.onerror = function () {
      showResult('讀取檔案失敗', true);
      uploadBtn.disabled = false;
      hideProgress();
    };
    reader.readAsDataURL(file);
  });
})();
