# OBE-Project GCP 部署環境 (Windows)：開啟 Cloud Functions 等 API
# 用法: .\setup_gcp.ps1 obe-project-485614

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = $env:PROJECT_ID
)

if (-not $ProjectId) {
    $ProjectId = $args[0]
}
if (-not $ProjectId) {
    Write-Host "用法: .\setup_gcp.ps1 obe-project-485614"
    Write-Host "或: `$env:PROJECT_ID='obe-project-485614'; .\setup_gcp.ps1"
    exit 1
}

Write-Host "專案 ID: $ProjectId"
gcloud config set project $ProjectId

Write-Host ""
Write-Host "正在開啟 Cloud Resource Manager API..."
gcloud services enable cloudresourcemanager.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "正在開啟 Cloud Functions API..."
gcloud services enable cloudfunctions.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "正在開啟 Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "正在開啟 Eventarc API..."
gcloud services enable eventarc.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "正在開啟 Cloud Run API (Gen2 函式需要)..."
gcloud services enable run.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "正在開啟 Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "完成。Cloud Functions、Cloud Build、Eventarc、Cloud Run、Secret Manager 已開啟。"
Write-Host "若要檢查已部署的函式："
Write-Host "  gcloud functions list --project=$ProjectId --gen2"
