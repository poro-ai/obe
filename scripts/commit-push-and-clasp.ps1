# OBE-Project：commit + clasp push + git push 一鍵執行
# 用法: .\scripts\commit-push-and-clasp.ps1 ["commit message"]
# 若未給訊息則使用預設: "chore: sync repo and GAS"

param([string]$Message = "chore: sync repo and GAS")

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $ProjectRoot

$status = git status --short
if (-not $status) {
    Write-Host "[略過] 無變更可提交。" -ForegroundColor Yellow
} else {
    git add -A
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (Test-Path ".clasp.json") {
    Write-Host "[GAS] 正在 clasp push..." -ForegroundColor Cyan
    npx @google/clasp push --force 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[警告] clasp push 失敗，繼續 git push。" -ForegroundColor Yellow
    }
} else {
    Write-Host "[略過] 無 .clasp.json，不執行 clasp push。" -ForegroundColor Yellow
}

Write-Host "[Git] 正在 git push origin main..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[完成] commit + clasp + push 完成。" -ForegroundColor Green
