/**
 * 前端與後端 GCF 通訊起點
 * 以 POST 送出 { bucket, blob_path } 至 parse_pdf 端點
 */

(function () {
  const apiUrlEl = document.getElementById('apiUrl');
  const bucketEl = document.getElementById('bucket');
  const blobPathEl = document.getElementById('blobPath');
  const submitBtn = document.getElementById('submit');
  const resultEl = document.getElementById('result');

  function showResult(text, isError) {
    resultEl.textContent = text;
    resultEl.className = isError ? 'error' : '';
  }

  submitBtn.addEventListener('click', async function () {
    const apiUrl = (apiUrlEl.value || '').trim();
    const bucket = (bucketEl.value || '').trim();
    const blobPath = (blobPathEl.value || '').trim();

    if (!apiUrl) {
      showResult('請輸入後端 API 網址（GCF 部署後的 URL）', true);
      return;
    }
    if (!bucket || !blobPath) {
      showResult('請輸入 GCS Bucket 名稱與 PDF 路徑（blob_path）', true);
      return;
    }

    submitBtn.disabled = true;
    showResult('請求中…');

    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bucket, blob_path: blobPath }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        showResult('錯誤 ' + res.status + ': ' + (data.error || res.statusText), true);
        return;
      }

      const count = data.count != null ? data.count : (data.pages && data.pages.length);
      showResult(
        '成功。共 ' + (count || 0) + ' 筆頁面。\n\n' +
        JSON.stringify(data, null, 2)
      );
    } catch (err) {
      showResult('請求失敗: ' + err.message, true);
    } finally {
      submitBtn.disabled = false;
    }
  });
})();
