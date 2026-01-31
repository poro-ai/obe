#!/usr/bin/env bash
# OBE-Project GCP 基礎設施設定
# 開啟 Vertex AI 與 Secret Manager API，供專案使用

set -e

# 從環境變數或第一個參數取得專案 ID
PROJECT_ID="${1:-${PROJECT_ID}}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "用法: ./setup_project.sh [PROJECT_ID]"
  echo "或設定環境變數: export PROJECT_ID=your-project-id"
  exit 1
fi

echo "專案 ID: $PROJECT_ID"
echo "正在設定 gcloud 預設專案..."
gcloud config set project "$PROJECT_ID"

echo ""
echo "正在開啟 Vertex AI API (aiplatform.googleapis.com)..."
gcloud services enable aiplatform.googleapis.com --project="$PROJECT_ID"

echo ""
echo "正在開啟 Secret Manager API (secretmanager.googleapis.com)..."
gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"

echo ""
echo "完成。已啟用："
echo "  - aiplatform.googleapis.com (Vertex AI)"
echo "  - secretmanager.googleapis.com (Secret Manager)"
