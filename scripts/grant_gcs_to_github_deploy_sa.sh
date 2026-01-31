#!/usr/bin/env bash
# OBE-Project：為 GAS 使用的服務帳號授予 GCS bucket 寫入權限
# 解決 GCS upload failed: 403 ... does not have storage.objects.create access
# 請在本機已登入 gcloud 且具備該專案 IAM 權限時執行

set -e
PROJECT_ID="obe-project-485614"
BUCKET="obe-files"
SA="github-deploy-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "即將為服務帳號授予 GCS 寫入權限："
echo "  專案: $PROJECT_ID"
echo "  Bucket: gs://$BUCKET"
echo "  服務帳號: $SA"
echo ""

if gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="serviceAccount:$SA" \
  --role="roles/storage.objectCreator" \
  --project="$PROJECT_ID"; then
  echo ""
  echo "完成。請再試一次 GAS 上傳 PDF。"
else
  echo "若失敗，可改用: gsutil iam ch serviceAccount:${SA}:objectCreator gs://$BUCKET"
  exit 1
fi
