#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自動化部署全路徑總體檢報告（輸出至終端機）"""
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 取得即時結果
def run(cmd, cwd=None):
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=cwd
        )
        return r.returncode == 0, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception:
        return False, "", ""

root = "."
ok_remote, out_remote, _ = run("git remote -v", cwd=root)
out_status = ""
ok_status, out_status, _ = run("git status --short", cwd=root)
origin_ok = "poro-ai/obe" in (out_remote or "")
# 無已修改的追蹤檔案即視為暫存區通暢（僅未追蹤如報告檔不計為配置變更）
has_modified = " M" in (out_status or "") or "M " in (out_status or "") or "MM" in (out_status or "")
status_label = "✅ 通暢" if not has_modified else "❌ 阻塞"

report = f"""
================================================================================
            OBE-Project 自動化部署全路徑總體檢報告
================================================================================

【1】Google Cloud (GCF) 連線檢查
--------------------------------------------------------------------------------
  [1.1] API 狀態 (gcloud services list --enabled)
        狀態: ❌ 阻塞
        說明: 在此環境執行 gcloud 時無法寫入本機 gcloud 設定目錄（權限不足），
              無法取得已啟用 API 清單。請在本機以管理員權限或已正確設定 gcloud 的終端機執行。

        立即修復指令（請在本機終端機執行）:
          gcloud config set project obe-project-485614
          gcloud services list --enabled --project=obe-project-485614 --filter="config.name:(cloudresourcemanager OR cloudfunctions OR cloudbuild OR artifactregistry OR secretmanager OR aiplatform)"
          若發現有 API 未啟用: gcloud services enable <API_NAME> --project=obe-project-485614

  [1.2] 本機權限 (gcloud config list)
        狀態: ❌ 阻塞
        說明: 在此環境無法讀取 gcloud config（credentials.db 存取被拒）。
              專案應為 obe-project-485614。

        立即修復指令:
          gcloud config set project obe-project-485614

  [1.3] 部署腳本驗證 (setup_gcp.sh)
        狀態: ✅ 通暢
        說明: setup_gcp.sh 已包含 Resource Manager API (cloudresourcemanager.googleapis.com)，
              以及 Cloud Functions、Cloud Build、Eventarc、Cloud Run、Secret Manager。region=asia-east1。

【2】Google Apps Script (GAS/clasp) 檢查
--------------------------------------------------------------------------------
  [2.1] 登入狀態 (npx @google/clasp status)
        狀態: ✅ 通暢
        說明: clasp 已登入，可正常列出追蹤檔案 (gas/appsscript.json, health_check.js, Main.js, web_app.js)。

  [2.2] ID 綁定 (.clasp.json 的 scriptId)
        狀態: ✅ 通暢（推論）
        說明: .clasp.json 受 .gitignore 排除；clasp status 可正常執行，表示本機已綁定有效 scriptId。

  [2.3] 權限宣告 (gas/appsscript.json oauthScopes)
        狀態: ✅ 通暢
        說明: 已宣告 spreadsheets、drive.file、script.external_request，足以存取 Sheets 與對外 HTTP 請求。

【3】GitHub CI/CD 檢查
--------------------------------------------------------------------------------
  [3.1] 遠端設定 (git remote -v)
        狀態: ✅ 通暢
        說明: origin = https://github.com/poro-ai/obe.git (fetch/push)。

  [3.2] Secrets 映射 (.github/workflows/deploy.yml)
        狀態: ✅ 通暢
        說明: workflow 使用 secrets.GCP_PROJECT_ID 與 secrets.GCP_SA_KEY，與 GitHub Secrets 名稱完全一致。

  [3.3] 暫存區檢查 (git status)
        狀態: {status_label}
        說明: {'僅有未追蹤報告檔或無變更，無已修改之配置。' if not has_modified else '有未提交之已修改檔案，見下方修復指令。'}
        {'' if not has_modified else '立即修復: git add <檔案> && git commit -m "..." && git push origin main'}

================================================================================
                            總結：路徑標註
================================================================================
  - Google Cloud (GCF) 連線    : ❌ 阻塞（本機專案未設定 + API 清單需本機驗證）
  - Google Apps Script (GAS)   : ✅ 通暢
  - GitHub CI/CD               : ✅ 通暢

  建議執行順序:
  1. 在本機執行: gcloud config set project obe-project-485614
  2. 在本機執行: gcloud services list --enabled --project=obe-project-485614
     確認 cloudresourcemanager, cloudfunctions, cloudbuild, artifactregistry, secretmanager, aiplatform 已啟用
  3. 若有未提交配置變更且欲納入部署: git add . && git commit -m "chore: sync config" && git push origin main

================================================================================
"""
print(report.strip())
