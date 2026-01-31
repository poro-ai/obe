# OBE-Project GAS 測試環境推送腳本 (Windows)
# 執行 clasp push 將 gas/ 推送到測試環境，並顯示編輯器連結

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Set-Location $ProjectRoot

# 檢查 .clasp.json 是否存在且含 scriptId
$claspPath = Join-Path $ProjectRoot ".clasp.json"
if (-not (Test-Path $claspPath)) {
    Write-Host "[錯誤] 找不到 .clasp.json。請先執行 clasp create 或手動建立 .clasp.json 並填入 scriptId。" -ForegroundColor Red
    exit 1
}

$clasp = Get-Content $claspPath -Raw | ConvertFrom-Json
$scriptId = $clasp.scriptId
if ([string]::IsNullOrWhiteSpace($scriptId)) {
    Write-Host "[錯誤] .clasp.json 中 scriptId 為空。請在 Google Apps Script 建立專案後，將 scriptId 填入 .clasp.json。" -ForegroundColor Red
    exit 1
}

Write-Host "正在推送 gas/ 至測試環境 (scriptId: $scriptId)..." -ForegroundColor Cyan
npx clasp push 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[錯誤] clasp push 失敗。" -ForegroundColor Red
    exit $LASTEXITCODE
}

$editorUrl = "https://script.google.com/home/projects/${scriptId}/edit"
Write-Host ""
Write-Host "推送完成。測試環境編輯器連結：" -ForegroundColor Green
Write-Host $editorUrl -ForegroundColor Yellow
Write-Host ""
Write-Host "是否在瀏覽器開啟? (Y/N): " -NoNewline
$open = Read-Host
if ($open -eq "Y" -or $open -eq "y") {
    Start-Process $editorUrl
}
