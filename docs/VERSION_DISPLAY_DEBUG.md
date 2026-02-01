# 版本資訊沒出現 — 如何確認是「code 沒更新」還是「code 有問題」

版本會出現在三處：**Slides 首頁卡片**、**Slides 側邊欄底部**、**編輯器／上傳頁**。依下面順序檢查。

---

## 一、先確認本機 code 有沒有版本相關程式

在本機專案根目錄執行（會檢查 `gas/` 裡是否有該有的程式）：

```bash
python scripts/verify_version_in_gas.py
```

若有任一步驟失敗，代表本機 code 不完整，先補齊或還原再往下做。

---

## 二、確認 GAS 專案已收到最新 code（code 有沒有更新到）

1. **推送到 Apps Script**
   ```bash
   npx clasp push
   ```
   確認輸出沒有錯誤，且包含 `Main.js`、`web_app.js`、`sidebar.html`。

2. **在 Apps Script 編輯器裡肉眼確認**
   - 開啟你的 OBE 專案（script.google.com）。
   - **Main.js**：搜尋 `版本：v` 或 `getVersion`，應看到首頁卡片裡有 `版本：v` + version 變數。
   - **web_app.js**：搜尋 `getVersion`、`BACKEND_VERSION`，應有 `function getVersion()` 與 `var BACKEND_VERSION = '1.0.06'`（第三碼 2 位數，或你目前的版號）。
   - **sidebar.html**：搜尋 `sidebar-version`、`getVersion()`，應有顯示「OBE v」與呼叫 `google.script.run...getVersion()`。

若編輯器裡**沒有**這些內容 → **code 沒更新到**：再執行一次 `clasp push`，或確認 `.clasp.json` 的 `scriptId` 是正確的專案。

若編輯器裡**有**這些內容 → code 已更新，問題多半是「執行到的是舊版」或「getVersion 沒被呼叫到」，接下一段。

---

## 三、確認執行到的是「最新版」（排除快取／舊部署）

- **首頁卡片**（OBE 說明 + 「開啟 AI 解析側邊欄」）
  - 在簡報右側，先**關掉**附加元件面板，再重新從「擴充功能」或首頁進入，讓卡片重新載入。
  - 若仍沒有「版本：v1.0.06」這行 → 可能是 **getVersion 未被呼叫或回傳空**（見下方「可能問題」）。

- **側邊欄**
  - 關閉側邊欄後再重新開啟（或重新整理簡報頁再開）。
  - 看底部是「OBE v1.0.06」、「OBE v—」還是「OBE v?」：
    - **OBE v1.0.06**：正常。
    - **OBE v—**：可能沒呼叫到 getVersion，或回傳空。
    - **OBE v?**：有呼叫 getVersion 但失敗（我們有加 withFailureHandler）。

- **測試安裝用哪一版**
  - 從「Apps Script 編輯器」安裝的測試，預設用**目前儲存的程式**（Head），不需要另建「部署版本」。
  - 若你有用「部署」→「測試部署」的網址安裝，要確認該部署對應的**版本**是剛 push 過的那一版。

---

## 四、如何判斷是「code 有問題」還是「只是沒更新／快取」

| 你看到的 | 較可能原因 |
|----------|------------|
| 首頁卡片完全沒有「版本：v…」這一行 | code 沒更新到 GAS（Main.js 沒有版本那行），或卡片是舊快取 → 先做二、三。 |
| 首頁卡片有「版本：v—」 | getVersion 沒被呼叫到或回傳空 → 可能是 **web_app.js 沒被載入**（見下方）。 |
| 側邊欄「OBE v?」 | getVersion 有被呼叫但執行失敗（權限或找不到函式）。 |
| 側邊欄一直是「OBE v—」 | 沒呼叫到或回傳空；或 HTML 仍是舊版（快取）。 |

**若確認 code 已更新（二、三都做過）仍異常：**

- **首頁卡片顯示「版本：v—」**
  - 在 GAS 專案裡，`getVersion` 定義在 **web_app.js**，首頁卡片在 **Main.js** 的 `onSlidesHomepage` 裡呼叫。
  - 若同一個 Apps Script 專案有同時包含 Main.js 與 web_app.js，理論上會共用全域，`getVersion()` 應可用。
  - **檢查**：在 Apps Script 編輯器左側檔案列表，確認有 **web_app.js**（或對應的檔名）。若沒有，代表 clasp 沒把 web_app.js 推上去，或推錯專案。

- **側邊欄「OBE v?」**
  - 代表 `google.script.run.getVersion()` 有執行但失敗（例如權限、或專案裡沒有 getVersion）。同上，確認 web_app.js 在專案裡且已儲存。

---

## 五、快速對照：版本顯示來源

| 顯示位置 | 程式位置 | 如何取得版號 |
|----------|----------|----------------|
| Slides 首頁卡片 | gas/Main.js `onSlidesHomepage` | `getVersion()`（定義在 web_app.js） |
| Slides 側邊欄底部 | gas/sidebar.html | `google.script.run.getVersion()` |
| 編輯器／上傳頁 | frontend/*.html + script.js | GET GAS Web App URL 或 JSONP `callback` |

首頁與側邊欄都依賴同一個 GAS 專案裡的 **getVersion()**；若兩處都沒有版號，先確認 **web_app.js 是否在該專案內並已推送**。

---

## 六、gasUrl 已改 /exec 仍不 work（編輯器在 GitHub Pages 等跨域）

編輯器在 `poro-ai.github.io`、gasUrl 為 `script.google.com` 時，版本與解析結果都用 **JSONP** 請求。若已改為 /exec 仍顯示「OBE v—」，依序檢查：

### 6.1 部署的「誰可以存取」必須允許未登入

1. 在 GAS：**部署** → **管理部署**。
2. 點選你的 Web App 部署右側 **鉛筆** 編輯。
3. **誰可以存取** 必須是 **「所有人」**（或至少「任何擁有 Google 帳戶的使用者」）。若為「僅我自己」，從編輯器（未以你身分登入的請求）會拿不到回應，版號與解析結果都會失敗。
4. 儲存後可再**新增部署**一次，取得新的 /exec 網址（若曾改過存取設定）。

### 6.2 直接開 /exec 網址確認有回傳 JSON

1. 在瀏覽器**新分頁**開啟你的 gasUrl（例如 `https://script.google.com/macros/s/xxx/exec`），**不要**加任何參數。
2. 應看到**純文字 JSON**，例如：`{"message":"Success","timestamp":"...","params":{},"version":"1.0.06"}`。
3. 若看到登入頁、錯誤頁或空白 → 表示該部署不允許未登入存取，或 URL 錯誤，請回到 6.1 並確認複製的是「網路應用程式」的 /exec 網址。

### 6.3 在編輯器頁面用開發者工具試 JSONP

#### 詳細執行步驟

1. **開啟編輯器頁**
   - 用瀏覽器打開你的編輯器網址，例如：  
     `https://poro-ai.github.io/obe/frontend/editor.html?presentationId=xxx&gasUrl=https%3A%2F%2Fscript.google.com%2Fmacros%2Fs%2F...%2Fexec`  
   - 確保網址裡的 `gasUrl` 已經是 **/exec** 結尾（不是 /dev）。

2. **打開開發者工具**
   - Windows：按鍵盤 **F12**，或 **Ctrl + Shift + I**。
   - Mac：按 **Cmd + Option + I**。
   - 或：在頁面空白處按右鍵 → 選「**檢查**」或「**Inspect**」。

3. **切到 Console 分頁**
   - 在開發者工具上方找到 **Console**（主控台）分頁，點一下。
   - 下方會出現一個可輸入文字的區域（通常有 `>` 提示）。

4. **複製下面整段程式**
   - 從 `(function () {` 複製到最後的 `})();`，**整段**複製（含第一行和最後一行）。

5. **把 YOUR_GAS_EXEC_URL 換成你的 /exec 網址**
   - 在複製的程式裡找到這一行：  
     `var url = 'YOUR_GAS_EXEC_URL';`
   - 把 **YOUR_GAS_EXEC_URL** 整串（含單引號內）換成你的 GAS Web App 網址。
   - 範例（請改成你自己的網址）：  
     `var url = 'https://script.google.com/macros/s/AKfycbyCliwz6gojLlddPYNNbVQppSa220MzJS0uk79-TyUrZtarU4wlZIAeV2irXk-t9prBRw/exec';`
   - 注意：網址**不要**加結尾斜線、**不要**加 `?` 或參數，結尾就是 `.../exec` 然後單引號 `';`。

6. **貼到 Console 並執行**
   - 在 Console 輸入區按一下（確保游標在裡面）。
   - **Ctrl + V**（Mac：**Cmd + V**）貼上你改好的整段程式。
   - 按 **Enter** 執行。

7. **看 Console 結果**
   - 若成功：會出現一行類似 **「版本: 1.0.06」**（或你目前的版號）→ 表示 GAS 與 JSONP 正常。
   - 若失敗：會出現 **「JSONP 載入失敗」** 或 **紅色 SyntaxError** → 表示請求失敗或 GAS 回傳了非 JavaScript，請回到 6.1、6.2 檢查部署與網址。

---

**程式碼（替換 YOUR_GAS_EXEC_URL 後整段貼到 Console）：**

```javascript
(function () {
  var url = 'YOUR_GAS_EXEC_URL';
  var cbName = 'test_ver_' + Date.now();
  window[cbName] = function (data) {
    console.log('版本:', data && data.version);
    delete window[cbName];
  };
  var s = document.createElement('script');
  s.src = url + (url.indexOf('?') >= 0 ? '&' : '?') + 'callback=' + cbName;
  s.onerror = function () { console.error('JSONP 載入失敗'); delete window[cbName]; };
  document.head.appendChild(s);
})();
```

### 6.4 確認編輯器用的 gasUrl 沒有被改壞

- 若你是從側邊欄「在瀏覽器開啟編輯器」進入，gasUrl 會來自 **GAS 專案內容** 的 **GAS_WEB_APP_URL**。
- 請在 GAS：**專案設定**（齒輪）→ **指令碼內容** → 確認 **GAS_WEB_APP_URL** 為完整的 **/exec** 網址（結尾是 `exec`，沒有 `/dev`，且沒有多餘斜線）。
- 改完後重新在側邊欄點「在瀏覽器開啟編輯器」，讓新 gasUrl 帶入編輯器。
