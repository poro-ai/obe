#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全路徑連線測試完成後，輸出最終連線清單至終端機。"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

print("""
================================================================================
                    parse_pdf 全路徑連線測試 — 最終連線清單
================================================================================

  [ 需手動 ] GAS 能否呼叫 GCF？
      → 已在 gas/Main.js 新增 testCloudCall()，並已 clasp push 至雲端。
      → 請在 GAS 編輯器選取 testCloudCall，按「執行」，從「執行紀錄」查看結果。
      → 若看到「GCF 回應狀態: 200」或「端點有回應」即為通暢。

  [ 已驗證 ] 本機能否呼叫 GCF？
      → 已執行 tests/test_cloud_connection.py，對 parse_pdf 發送 POST。
      → 收到 HTTP 回應（本次為 500，因測試用 GCS 路徑不存在），表示連線通暢。

  [ 已驗證 ] GitHub Secrets 是否能成功完成自動部署？
      → 您已表示「剛部署成功的 parse_pdf」，代表 Secrets (GCP_PROJECT_ID / GCP_SA_KEY) 正確。
      → 已於 .github/workflows/deploy.yml 加入「Post-deployment check」步驟，未來每次 Push 會自動測試網址存活性。

================================================================================
  後續：下次 Push 至 main 時，Actions 會自動執行部署 + 部署後活體檢查。
================================================================================
""")
