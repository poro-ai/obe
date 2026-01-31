# OBE-Project：為 GAS 使用的服務帳號授予 GCS bucket 寫入權限
# 解決 GCS upload failed: 403 ... does not have storage.objects.create access
# 請在本機已登入 gcloud 且具備該專案 IAM 權限時執行

$ErrorActionPreference = "Stop"
$ProjectId = "obe-project-485614"
$Bucket = "obe-files"
$ServiceAccount = "github-deploy-sa@${ProjectId}.iam.gserviceaccount.com"

Write-Host "即將為服務帳號授予 GCS 寫入權限：" -ForegroundColor Cyan
Write-Host "  專案: $ProjectId" -ForegroundColor Gray
Write-Host "  Bucket: gs://$Bucket" -ForegroundColor Gray
Write-Host "  服務帳號: $ServiceAccount" -ForegroundColor Gray
Write-Host ""

# 使用 gcloud storage (新) 或 gsutil (舊) 授予 Storage Object Creator
try {
    gcloud storage buckets add-iam-policy-binding "gs://$Bucket" `
        --member="serviceAccount:$ServiceAccount" `
        --role="roles/storage.objectCreator" `
        --project="$ProjectId" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "gcloud storage failed" }
} catch {
    Write-Host "若上方失敗，可改用 gsutil：" -ForegroundColor Yellow
    Write-Host "  gsutil iam ch serviceAccount:${ServiceAccount}:objectCreator gs://$Bucket" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "完成。請再試一次 GAS 上傳 PDF。" -ForegroundColor Green
