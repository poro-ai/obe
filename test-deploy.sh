#!/usr/bin/env bash
# OBE-Project GAS 測試環境推送腳本 (macOS/Linux)
# 執行 clasp push 將 gas/ 推送到測試環境，並顯示編輯器連結

set -e
cd "$(dirname "$0")"

CLASP_JSON=".clasp.json"
if [[ ! -f "$CLASP_JSON" ]]; then
  echo "[錯誤] 找不到 .clasp.json。請先執行 clasp create 或手動建立 .clasp.json 並填入 scriptId。"
  exit 1
fi

SCRIPT_ID=$(node -e "const j=JSON.parse(require('fs').readFileSync('.clasp.json','utf8')); console.log(j.scriptId||'')")
if [[ -z "$SCRIPT_ID" ]]; then
  echo "[錯誤] .clasp.json 中 scriptId 為空。請在 Google Apps Script 建立專案後，將 scriptId 填入 .clasp.json。"
  exit 1
fi

echo "正在推送 gas/ 至測試環境 (scriptId: $SCRIPT_ID)..."
npx clasp push

EDITOR_URL="https://script.google.com/home/projects/${SCRIPT_ID}/edit"
echo ""
echo "推送完成。測試環境編輯器連結："
echo "$EDITOR_URL"
echo ""
echo "可執行以下指令在瀏覽器開啟: clasp open"
