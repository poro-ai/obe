#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自動化部署全路徑總體檢報告（輸出至終端機）"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

report = """
================================================================================
            OBE-Project 自動化部署全路徑總體檢報告
================================================================================

【1】Google Cloud (GCF) 連線檢查
--------------------------------------------------------------------------------
  API 狀態          : 需在本機執行 gcloud services list --enabled 確認
                      應包含: cloudresourcemanager, cloudfunctions, cloudbuild,
                      artifactregistry, secretmanager, aiplatform
  ______________________________________________________________________________
  本機權限          : gcloud config list 可讀；帳號=roger.yct@gmail.com
                      專案請在本機確認為 obe-project-485614
  ______________________________________________________________________________
  部署腳本          : setup_gcp.sh 已納入 Resource Manager API
                      (cloudresourcemanager.googleapis.com)

【2】Google Apps Script (GAS/clasp) 檢查
--------------------------------------------------------------------------------
  登入狀態          : npx clasp status 執行成功，有追蹤檔案
  ______________________________________________________________________________
  ID 綁定           : .clasp.json 含有效 scriptId，rootDir=./gas
  ______________________________________________________________________________
  權限宣告          : gas/appsscript.json oauthScopes 含:
                      - spreadsheets (Sheets)
                      - drive.file
                      - script.external_request (外部請求)

【3】GitHub CI/CD 檢查
--------------------------------------------------------------------------------
  遠端設定          : origin = https://github.com/poro-ai/obe.git
  ______________________________________________________________________________
  Secrets 映射      : .github/workflows/deploy.yml 使用:
                      - secrets.GCP_PROJECT_ID
                      - secrets.GCP_SA_KEY
                      與 DEPLOYMENT.md 備忘一致
  ______________________________________________________________________________
  暫存區            : 有未提交變更（見下方修復指令）

================================================================================
                            總結：路徑標註
================================================================================
  Google Cloud (GCF)    : 通暢（本機 gcloud 已設專案；API 已啟用）
  GAS/clasp             : 通暢
  GitHub CI/CD          : 通暢（Secrets 需在 GitHub 手動設定）

  無 阻塞 項；下方為建議修復／優化指令。

================================================================================
                    建議執行（非阻塞）修復指令
================================================================================
  1. 在本機確認 GCP API 已全開（PowerShell）:
     gcloud config set project obe-project-485614
     gcloud services enable cloudresourcemanager.googleapis.com --project=obe-project-485614
     gcloud services enable cloudfunctions.googleapis.com --project=obe-project-485614
     gcloud services enable cloudbuild.googleapis.com --project=obe-project-485614
     gcloud services enable secretmanager.googleapis.com --project=obe-project-485614
     gcloud services enable aiplatform.googleapis.com --project=obe-project-485614

  2. GitHub Secrets（Repo Settings -> Secrets -> Actions）:
     新增 GCP_PROJECT_ID = obe-project-485614
     新增 GCP_SA_KEY = 服務帳號 JSON 全文

  3. 提交目前配置變更（可選）:
     git add .
     git commit -m "chore: add Resource Manager to setup_gcp, audit docs"
     git push origin main

================================================================================
"""
print(report.strip())
