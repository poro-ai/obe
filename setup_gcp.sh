#!/usr/bin/env bash
# OBE-Project GCP 部署環境：開啟 Cloud Functions API 並可選驗證現有函式
# 與 setup_project.sh 互補（本腳本著重 GCF 部署所需 API）

set -e

PROJECT_ID="${1:-${PROJECT_ID}}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "用法: ./setup_gcp.sh [PROJECT_ID]"
  echo "或設定環境變數: export PROJECT_ID=your-project-id"
  exit 1
fi

echo "專案 ID: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo ""
echo "正在開啟 Cloud Resource Manager API (cloudresourcemanager.googleapis.com)..."
gcloud services enable cloudresourcemanager.googleapis.com --project="$PROJECT_ID"

echo ""
echo "正在開啟 Cloud Functions API (cloudfunctions.googleapis.com)..."
gcloud services enable cloudfunctions.googleapis.com --project="$PROJECT_ID"

echo ""
echo "正在開啟 Cloud Build API (cloudbuild.googleapis.com)..."
gcloud services enable cloudbuild.googleapis.com --project="$PROJECT_ID"

echo ""
echo "正在開啟 Eventarc API (eventarc.googleapis.com)..."
gcloud services enable eventarc.googleapis.com --project="$PROJECT_ID"

echo ""
echo "正在開啟 Cloud Run API (run.googleapis.com，Gen2 函式需要)..."
gcloud services enable run.googleapis.com --project="$PROJECT_ID"

echo ""
echo "正在開啟 Secret Manager API (secretmanager.googleapis.com)..."
gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"

echo ""
echo "完成。Cloud Functions、Cloud Build、Eventarc、Cloud Run、Secret Manager 已開啟。"
echo "若要檢查已部署的函式："
echo "  gcloud functions list --project=$PROJECT_ID --gen2"
echo "若要查看單一函式："
echo "  gcloud functions describe parse_pdf --region=asia-east1 --gen2 --project=$PROJECT_ID"
